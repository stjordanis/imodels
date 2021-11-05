import json
import pandas as pd
from sklearn.utils import validation

import gosdt

from imodels.tree.gosdt.tree_classifier import TreeClassifier
from imodels.util import rule


class GOSDTClassifier:
    def __init__(self,
                 balance=False,
                 cancellation=True,
                 look_ahead=True,
                 similar_support=True,
                 feature_exchange=True,
                 continuous_feature_exchange=True,
                 rule_list=False,
                 diagnostics=False,
                 verbose=False,
                 regularization=0.05,
                 uncertainty_tolerance=0.0,
                 upperbound=0.0,
                 model_limit=1,
                 precision_limit=0,
                 stack_limit=0,
                 tile_limit=0,
                 time_limit=0,
                 worker_limit=1,
                 costs="",
                 model="",
                 profile="",
                 timing="",
                 trace="",
                 tree=""):
        self.balance = balance
        self.cancellation = cancellation
        self.look_ahead = look_ahead
        self.similar_support = similar_support
        self.feature_exchange = feature_exchange
        self.continuous_feature_exchange = continuous_feature_exchange
        self.rule_list = rule_list
        self.diagnostics = diagnostics
        self.verbose = verbose
        self.regularization = regularization
        self.uncertainty_tolerance = uncertainty_tolerance
        self.upperbound = upperbound
        self.model_limit = model_limit
        self.precision_limit = precision_limit
        self.stack_limit = stack_limit
        self.tile_limit = tile_limit
        self.time_limit = time_limit
        self.worker_limit = worker_limit
        self.costs = costs
        self.model = model
        self.profile = profile
        self.timing = timing
        self.trace = trace
        self.tree = tree

    def load(self, path):
        """
        Parameters
        ---
        path : string
            path to a JSON file representing a model
        """
        with open(path, 'r') as model_source:
            result = model_source.read()
        result = json.loads(result)
        self.tree_ = TreeClassifier(result[0])
        
    def status(self):
        return gosdt.status()

    def fit(self, X, y, feature_names=None):
        """
        Parameters
        ---
        X : matrix-like, shape = [n_samples, m_features]
            matrix containing the training samples and features
        y : array-like, shape = [n_samples, 1]
            column containing the correct label for each sample in X

        Modifies
        ---
        trains the model so that this model instance is ready for prediction
        """
        if not isinstance(X, pd.DataFrame):
            self.feature_names_ = list(rule.get_feature_dict(X.shape[1], feature_names).keys())
            X = pd.DataFrame(X, columns=self.feature_names_)
        else:
            self.feature_names_ = X.columns
        
        if not isinstance(y, pd.DataFrame):
            y = pd.DataFrame(y, columns=['target'])
        
        # gosdt extension expects serialized CSV, which we generate via pandas
        dataset_with_target = pd.concat((X, y), axis=1)

        # Perform C++ extension calls to train the model
        configuration = self._get_configuration()
        gosdt.configure(json.dumps(configuration, separators=(',', ':')))
        result = gosdt.fit(dataset_with_target.to_csv(index=False))

        result = json.loads(result)
        self.tree_ = TreeClassifier(result[0])

        # Record the training time, number of iterations, and graph size required
        self.time_ = gosdt.time()
        self.iterations_ = gosdt.iterations()
        self.size_ = gosdt.size()

        return self

    def predict(self, X):
        """
        Parameters
        ---
        X : matrix-like, shape = [n_samples by m_features]
            a matrix where each row is a sample to be predicted and each column is a feature to
            be used for prediction

        Returns
        ---
        array-like, shape = [n_sampels by 1] : a column where each element is the prediction
            associated with each row
        """
        validation.check_is_fitted(self)
        if not isinstance(X, pd.DataFrame):
            X = pd.DataFrame(X, columns=self.feature_names_)
        return self.tree_.predict(X)

    def error(self, X, y, weight=None):
        """
        Parameters
        ---
        X : matrix-like, shape = [n_samples by m_features]
            an n-by-m matrix of sample and their features
        y : array-like, shape = [n_samples by 1]
            an n-by-1 column of labels associated with each sample
        weight : real number
            an n-by-1 column of weights to apply to each sample's misclassification

        Returns
        ---
        real number : the inaccuracy produced by applying this model overthe given dataset, with
            optionals for weighted inaccuracy
        """
        validation.check_is_fitted(self)
        if not isinstance(X, pd.DataFrame):
            X = pd.DataFrame(X, columns=self.feature_names_)
        return self.tree_.error(X, y, weight=weight)

    def score(self, X, y, weight=None):
        """
        Parameters
        ---
        X : matrix-like, shape = [n_samples by m_features]
            an n-by-m matrix of sample and their features
        y : array-like, shape = [n_samples by 1]
            an n-by-1 column of labels associated with each sample
        weight : real number
            an n-by-1 column of weights to apply to each sample's misclassification

        Returns
        ---
        real number : the accuracy produced by applying this model overthe given dataset, with
            optionals for weighted accuracy
        """
        validation.check_is_fitted(self)
        if not isinstance(X, pd.DataFrame):
            X = pd.DataFrame(X, columns=self.feature_names_)
        return self.tree_.score(X, y, weight=weight)

    def __len__(self):
        """
        Returns
        ---
        natural number : The number of terminal nodes present in this tree
        """
        validation.check_is_fitted(self)
        return len(self.tree_)

    def leaves(self):
        """
        Returns
        ---
        natural number : The number of terminal nodes present in this tree
        """
        validation.check_is_fitted(self)
        return self.tree_.leaves()

    def nodes(self):
        """
        Returns
        ---
        natural number : The number of nodes present in this tree
        """
        validation.check_is_fitted(self)
        return self.tree_.nodes()

    def max_depth(self):
        """
        Returns
        ---
        natural number : the length of the longest decision path in this tree. A single-node tree
            will return 1.
        """
        validation.check_is_fitted(self)
        return self.tree_.maximum_depth()

    def latex(self):
        """
        Note
        ---
        This method doesn't work well for label headers that contain underscores due to underscore
            being a reserved character in LaTeX

        Returns
        ---
        string : A LaTeX string representing the model
        """
        validation.check_is_fitted(self)
        return self.tree_.latex()

    def json(self):
        """
        Returns
        ---
        string : A JSON string representing the model
        """
        validation.check_is_fitted(self)
        return self.tree_.json()

    def _get_configuration(self):
        return {
            "balance": self.balance,
            "cancellation": self.cancellation,
            "look_ahead": self.look_ahead,
            "similar_support": self.similar_support,
            "feature_exchange": self.feature_exchange,
            "continuous_feature_exchange": self.continuous_feature_exchange,
            "rule_list": self.rule_list,

            "diagnostics": self.diagnostics,
            "verbose": self.verbose,

            "regularization": self.regularization,
            "uncertainty_tolerance": self.uncertainty_tolerance,
            "upperbound": self.upperbound,

            "model_limit": self.model_limit,
            "precision_limit": self.precision_limit,
            "stack_limit": self.stack_limit,
            "tile_limit": self.tile_limit,
            "time_limit": self.time_limit,
            "worker_limit": self.worker_limit,

            "costs": self.costs,
            "model": self.model,
            "profile": self.profile,
            "timing": self.timing,
            "trace": self.trace,
            "tree": self.tree
        }