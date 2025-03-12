import numpy as np
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import Matern
from scipy.stats import norm

class BayesianOptimizer:
    def __init__(self, bounds, kernel=None, random_state=42):
        """
        初始化贝叶斯优化器
        
        Args:
            bounds: 参数空间边界，形如 [(x1_min, x1_max), (x2_min, x2_max), ...]
            kernel: GP的核函数，默认使用Matérn核
            random_state: 随机种子
        """
        self.bounds = np.array(bounds)
        self.dim = len(bounds)

        if kernel is None:
            kernel = Matern(length_scale=1.0, nu=2.5)
        
        self.gp = GaussianProcessRegressor(
            kernel=kernel,
            n_restarts_optimizer=5,
            random_state=random_state
        )

        self.X_observed = []
        self.y_observed = []
        self.best_value = -np.inf
        
    def expected_improvement(self, X):
        X = X.reshape(-1, self.dim)
        if len(self.X_observed) == 0:
            return np.ones(X.shape[0])

        mu, sigma = self.gp.predict(X, return_std=True)
        sigma = sigma.reshape(-1, 1)

        improvement = mu - self.best_value

        Z = improvement / (sigma + 1e-9)
        ei = improvement * norm.cdf(Z) + sigma * norm.pdf(Z)
        
        return ei.ravel()
    
    def suggest_next_point(self, n_restarts=25):
        from scipy.optimize import minimize

        best_x = None
        best_ei = -np.inf

        bounds = self.bounds
        for _ in range(n_restarts):
            x0 = np.random.uniform(bounds[:, 0], bounds[:, 1])

            result = minimize(
                lambda x: -self.expected_improvement(x),
                x0,
                bounds=bounds,
                method='L-BFGS-B'
            )
            
            if result.fun < -best_ei:
                best_ei = -result.fun
                best_x = result.x
                
        return best_x
    
    def update(self, X, y):
        X = np.array(X).reshape(-1, self.dim)
        y = np.array(y).ravel()
    
        # 修改检查方式
        if len(self.X_observed) == 0:
            self.X_observed = X
            self.y_observed = y
        else:
            self.X_observed = np.vstack((self.X_observed, X))
            self.y_observed = np.concatenate((self.y_observed, y))
    
        self.best_value = np.max(self.y_observed)
        self.gp.fit(self.X_observed, self.y_observed)

def example_usage():
    def objective_function(x):
        return -(x[0] - 2) ** 2 - (x[1] - 3) ** 2

    bounds = [(-5, 5), (-5, 5)]
    optimizer = BayesianOptimizer(bounds)

    n_initial = 5
    X_init = np.random.uniform([-5, -5], [5, 5], size=(n_initial, 2))
    y_init = [objective_function(x) for x in X_init]

    optimizer.update(X_init, y_init)

    n_iterations = 10
    for i in range(n_iterations):
        next_point = optimizer.suggest_next_point()

        next_value = objective_function(next_point)

        optimizer.update([next_point], [next_value])
        
        print(f"Iteration {i+1}:")
        print(f"Next point: {next_point}")
        print(f"Value: {next_value}")
        print(f"Best value so far: {optimizer.best_value}\n")

if __name__ == "__main__":
    example_usage()