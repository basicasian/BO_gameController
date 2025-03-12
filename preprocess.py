import numpy as np
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import Matern
import optuna
from scipy.optimize import minimize
import scipy.stats as stats

def accuracy(error,lam):
    return np.exp(-lam*error**2)

def res_speed(moving_time, jitter=0, alpha=0.5):
    return 1/(moving_time+alpha*jitter)

def error_calc(pos:list):
    n = len(pos)
    error = sum(pos)/n
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
        """Compute log prior (Gamma prior on exp(utilities))"""
        return sum(stats.gamma.logpdf(np.exp(u), self.prior_alpha, scale=1/self.prior_beta) + u for u in utilities)
    
    def objective(self, utilities, rankings):
        """Negative log posterior for optimization"""
        return -(self.log_likelihood(utilities, rankings) + self.log_prior(utilities))
    
    def fit(self, rankings):
        """Perform MAP estimation"""
        initial_utilities = np.zeros(self.n_candidates)
        result = minimize(
            lambda x: self.objective(x, rankings),
            initial_utilities,
            method='BFGS'
        )
        return np.exp(result.x)  # Return utilities in probability space

class PreferenceModel:
    def __init__(self, n_candidates):
        self.pl_model = PlackettLuce(n_candidates)
        self.gp_model = GPModel()
        
    def fit(self, rankings, features):
        """
        Fit both Plackett-Luce and GP models
        rankings: list of rankings
        features: array of feature vectors for each candidate
        """
        # First get utilities using Plackett-Luce
        utilities = self.pl_model.fit(rankings)
        
        # Use utilities as target values for GP
        self.gp_model.X_train = features
        self.gp_model.y_train = utilities
        self.gp_model.train()
    
    def predict(self, features):
        """Predict utilities for new candidates"""
        return self.gp_model.predict(features)

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

class HybridModel:
    def __init__(self, n_candidates, lambda_weight=0.5):
        self.pref_model = PreferenceModel(n_candidates)
        self.perf_model = PerformanceModel()
        self.lambda_weight = lambda_weight
    
    def fit(self, rankings, features, errors, moving_times, jitters=None):
        """
        训练混合模型
        
        Args:
            rankings: 排序数据列表
            features: 特征向量数组
            errors: 误差值数组
            moving_times: 移动时间数组
            jitters: 抖动值数组（可选）
        """
        self.perf_values = self.perf_model.evaluate_batch(
            errors, moving_times, jitters
        )
        self.pref_model.fit(rankings, features)
    
    def predict(self, features, errors, moving_times, jitters=None):
        pref_values, uncertainties = self.pref_model.predict(features)

        perf_values = self.perf_model.evaluate_batch(
            errors, moving_times, jitters
        )

        joint_values = (self.lambda_weight * perf_values + 
                       (1 - self.lambda_weight) * pref_values)

        scaled_uncertainties = (1 - self.lambda_weight) * uncertainties
        
        return joint_values, scaled_uncertainties

# 更新示例用法
def example_usage():
    n_candidates = 5
    n_rankings = 10
    
    # 生成随机数据
    rankings = [np.random.permutation(n_candidates) for _ in range(n_rankings)]
    features = np.random.rand(n_candidates, 3)
    errors = np.random.rand(n_candidates) * 0.5  # 随机误差值
    moving_times = np.random.rand(n_candidates) * 2  # 随机移动时间
    jitters = np.random.rand(n_candidates) * 0.1  # 随机抖动值
    
    # 创建并训练混合模型
    model = HybridModel(n_candidates, lambda_weight=0.7)
    model.fit(rankings, features, errors, moving_times, jitters)
    
    # 预测新样本
    new_features = np.random.rand(2, 3)
    new_errors = np.random.rand(2) * 0.5
    new_moving_times = np.random.rand(2) * 2
    new_jitters = np.random.rand(2) * 0.1
    
    joint_values, uncertainties = model.predict(
        new_features, new_errors, new_moving_times, new_jitters
    )
    
    return joint_values, uncertainties

if __name__ == '__main__':
    predicted_utilities, uncertainties = example_usage()
    print("Predicted utilities:", predicted_utilities)
    print("Uncertainties:", uncertainties)