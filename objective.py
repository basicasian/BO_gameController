import numpy as np
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import Matern
import optuna
from scipy.optimize import minimize
import scipy.stats as stats


def accuracy(error, lam):
    return np.exp(-lam * error ** 2)


def res_speed(moving_time, jitter=0, alpha=0.5):
    return 1 / (moving_time + alpha * jitter)


def error_calc(dis: list, scale: float = 0.02):
    mapped_pos = [x * scale for x in dis]
    n = len(mapped_pos)
    error = sum(mapped_pos) / n
    return error


def f_perf(accuracy_val, speed_val, w1=0.6):
    w2 = 1 - w1
    return w1 * accuracy_val + w2 * speed_val


class GPModel:
    def __init__(self, X_train=None, y_train=None):
        self.X_train = X_train
        self.y_train = y_train
        self.gp = None

    def objective(self, trial):
        nu = trial.suggest_categorical('nu', [0.5, 1.5, 2.5])
        length_scale = trial.suggest_float('length_scale', 0.1, 2.0)
        noise_level = trial.suggest_float('noise_level', 1e-10, 1e-1, log=True)

        kernel = Matern(length_scale=length_scale, nu=nu)

        gp = GaussianProcessRegressor(
            kernel=kernel,
            alpha=noise_level,
            n_restarts_optimizer=5,
            random_state=42
        )

        # Check if we have enough samples for cross-validation
        if len(self.X_train) < 5:
            # For small datasets, fit once and use negative mean squared error
            gp.fit(self.X_train, self.y_train)
            y_pred = gp.predict(self.X_train)
            return -np.mean((self.y_train - y_pred) ** 2)
        else:
            # For larger datasets, use cross-validation
            from sklearn.model_selection import cross_val_score
            scores = cross_val_score(gp, self.X_train, self.y_train,
                                     cv=min(5, len(self.X_train)),
                                     scoring='neg_mean_squared_error')
            return scores.mean()

    def train(self, n_trials=100):
        study = optuna.create_study(direction='maximize')
        study.optimize(self.objective, n_trials=n_trials)

        best_params = study.best_params
        kernel = Matern(
            length_scale=best_params['length_scale'],
            nu=best_params['nu']
        )

        self.gp = GaussianProcessRegressor(
            kernel=kernel,
            alpha=best_params['noise_level'],
            n_restarts_optimizer=5,
            random_state=42
        )
        self.gp.fit(self.X_train, self.y_train)

    def predict(self, X_test):
        if self.gp is None:
            raise ValueError("No train data")
        return self.gp.predict(X_test, return_std=True)


class PlackettLuce:
    def __init__(self, n_candidates):
        self.n_candidates = n_candidates
        self.prior_alpha = 1.0
        self.prior_beta = 1.0

    def compute_probability(self, ranking, utilities):
        """Compute Plackett-Luce probability for a given ranking"""
        prob = 1.0
        remaining = set(range(self.n_candidates))

        for rank in ranking:
            numerator = np.exp(utilities[rank])
            denominator = sum(np.exp(utilities[j]) for j in remaining)
            prob *= numerator / denominator
            remaining.remove(rank)

        return prob

    def log_likelihood(self, utilities, rankings):
        """Compute log likelihood of multiple rankings"""
        log_prob = 0
        for ranking in rankings:
            log_prob += np.log(self.compute_probability(ranking, utilities))
        return log_prob

    def log_prior(self, utilities):
    
        return sum(stats.gamma.logpdf(np.exp(u), self.prior_alpha, scale=1 / self.prior_beta) + u for u in utilities)

    def objective(self, utilities, rankings):
        return -(self.log_likelihood(utilities, rankings) + self.log_prior(utilities))

    def fit(self, rankings):
        initial_utilities = np.zeros(self.n_candidates)
        result = minimize(
            lambda x: self.objective(x, rankings),
            initial_utilities,
            method='BFGS'
        )
        return np.exp(result.x) 

class PreferenceModel:
    def __init__(self, n_candidates, pair=False, similar_comparison=False):
        self.pl_model = PlackettLuce(n_candidates)
        self.utilities = None
        self.pair = pair
        self.similar_comparison = similar_comparison
        self.n_candidates = n_candidates
        self.comparison_history = []
        self.similar_pairs = []
        
    def find_similar_preferences(self):
        if len(self.comparison_history) < 2:
            return []
            
        dominance = {}
        for winner, loser in self.comparison_history:
            if winner not in dominance:
                dominance[winner] = set()
            dominance[winner].add(loser)
        similar_pairs = []
        for i in dominance:
            for j in dominance:
                if i != j and dominance[i].intersection(dominance[j]):
                    if (i, j) not in self.similar_pairs and (j, i) not in self.similar_pairs:
                        similar_pairs.append((i, j))
                        
        return similar_pairs
        
    def verify_similar_pair(self, pair1, pair2):
        return self.comparison_history.append((pair1, pair2))

    def _convert_pairwise_to_rankings(self, pairwise_comparisons):
        rankings = []
        for winner, loser in pairwise_comparisons:
            rankings.append([winner, loser])
        return rankings

    def fit(self, comparisons):
        if self.pair:
            # Process pairwise comparisons
            rankings = self._convert_pairwise_to_rankings(comparisons)
        else:
            # Use original rankings directly
            rankings = comparisons
            
        self.utilities = self.pl_model.fit(rankings)
        return self.utilities

    def add_comparison(self, current_idx, is_better_than_previous):
        """Add a new pairwise comparison result"""
        if not self.pair:
            raise ValueError("This method is only available in pairwise mode")
        
        if current_idx > 0:  # Skip first item (baseline)
            prev_idx = current_idx - 1
            if is_better_than_previous:
                self.comparison_history.append((current_idx, prev_idx))
            else:
                self.comparison_history.append((prev_idx, current_idx))

    def predict(self):
        if self.utilities is None:
            raise ValueError("Model not fitted yet")
        return self.utilities


class PerformanceModel:
    def __init__(self):
        self.lam = 1.0
        self.alpha = 0.5

    def compute_performance(self, error, moving_time, jitter=0):
        acc = accuracy(error, self.lam)
        speed = res_speed(moving_time, jitter, self.alpha)
        return f_perf(acc, speed)

    def evaluate_batch(self, errors, moving_times, jitters=None):
        if jitters is None:
            jitters = np.zeros_like(errors)

        perf_values = np.array([
            self.compute_performance(e, mt, j)
            for e, mt, j in zip(errors, moving_times, jitters)
        ])
        return perf_values


def joint_score(params, errors, moving_times, jitters, rankings=None, lambda_weight=0.5):
    """
    params:
        [categorical_params, continuous_params]
        categorical_params: [cap_type, material_surface]
        continuous_params: [rocker_length, cap_size, spring_stiffness, damping_factor]
    """
    perf_model = PerformanceModel()
    perf_values = perf_model.evaluate_batch(errors, moving_times, jitters)

    if rankings is None:
        return perf_values

    pref_model = PreferenceModel(len(errors))
    pref_values = pref_model.fit(rankings)

    gp_perf = GPModel()
    gp_pref = GPModel()

    X = np.array([
        [
            *p[0],
            *p[1]
        ] 
        for p in params
    ])

    gp_perf.X_train = X
    gp_perf.y_train = perf_values
    gp_perf.train()

    gp_pref.X_train = X
    gp_pref.y_train = pref_values
    gp_pref.train()

    perf_pred, _ = gp_perf.predict(X)
    pref_pred, _ = gp_pref.predict(X)

    joint_values = lambda_weight * perf_pred + (1 - lambda_weight) * pref_pred
    
    return joint_values





