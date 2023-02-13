"""Test CompatibleAdaBoostClassifier."""
# Authors: Guillaume Lemaitre
#          Christos Aridas
#          Zhining Liu <zhining.liu@outlook.com>
# License: MIT

import numpy as np
import pytest
import sklearn
from sklearn.datasets import load_iris, make_classification
from sklearn.model_selection import train_test_split
from sklearn.utils._testing import assert_array_equal
from sklearn.utils.fixes import parse_version

from imbens.ensemble import CompatibleAdaBoostClassifier

sklearn_version = parse_version(sklearn.__version__)


@pytest.fixture
def imbalanced_dataset():
    return make_classification(
        n_samples=10000,
        n_features=3,
        n_informative=2,
        n_redundant=0,
        n_repeated=0,
        n_classes=3,
        n_clusters_per_class=1,
        weights=[0.01, 0.05, 0.94],
        class_sep=0.8,
        random_state=0,
    )


@pytest.mark.parametrize("algorithm", ["SAMME", "SAMME.R"])
def test_adaboost(imbalanced_dataset, algorithm):
    X, y = imbalanced_dataset
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, stratify=y, random_state=1
    )
    classes = np.unique(y)

    n_estimators = 500
    adaboost = CompatibleAdaBoostClassifier(
        n_estimators=n_estimators, algorithm=algorithm, random_state=0
    )
    adaboost.fit(X_train, y_train)
    assert_array_equal(classes, adaboost.classes_)

    # check that we have an ensemble of estimators with a
    # consistent size
    assert len(adaboost.estimators_) > 1

    # each estimator in the ensemble should have different random state
    assert len({est.random_state for est in adaboost.estimators_}) == len(
        adaboost.estimators_
    )

    # check the consistency of the feature importances
    assert len(adaboost.feature_importances_) == imbalanced_dataset[0].shape[1]

    # check the consistency of the prediction outpus
    y_pred = adaboost.predict_proba(X_test)
    assert y_pred.shape[1] == len(classes)
    assert adaboost.decision_function(X_test).shape[1] == len(classes)

    score = adaboost.score(X_test, y_test)
    assert score > 0.6, f"Failed with algorithm {algorithm} and score {score}"

    y_pred = adaboost.predict(X_test)
    assert y_pred.shape == y_test.shape


@pytest.mark.parametrize("algorithm", ["SAMME", "SAMME.R"])
def test_adaboost_sample_weight(imbalanced_dataset, algorithm):
    X, y = imbalanced_dataset
    sample_weight = np.ones_like(y)
    adaboost = CompatibleAdaBoostClassifier(algorithm=algorithm, random_state=0)

    # Predictions should be the same when sample_weight are all ones
    y_pred_sample_weight = adaboost.fit(X, y, sample_weight=sample_weight).predict(X)
    y_pred_no_sample_weight = adaboost.fit(X, y).predict(X)

    assert_array_equal(y_pred_sample_weight, y_pred_no_sample_weight)

    rng = np.random.RandomState(42)
    sample_weight = rng.rand(y.shape[0])
    y_pred_sample_weight = adaboost.fit(X, y, sample_weight=sample_weight).predict(X)

    with pytest.raises(AssertionError):
        assert_array_equal(y_pred_no_sample_weight, y_pred_sample_weight)
