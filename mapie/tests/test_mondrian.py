from copy import deepcopy

import numpy as np
import pytest
from sklearn.base import clone
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.datasets import (
    make_classification,
    make_multilabel_classification,
    make_regression
)
from sklearn.multioutput import MultiOutputClassifier
from sklearn.model_selection import ShuffleSplit

from mapie.calibration import MapieCalibrator
from mapie.classification import MapieClassifier
from mapie.conformity_scores import (
    AbsoluteConformityScore,
    APSConformityScore,
    GammaConformityScore,
    LACConformityScore,
    TopKConformityScore,
    RAPSConformityScore,
    ResidualNormalisedScore
)
from mapie.mondrian import MondrianCP
from mapie.multi_label_classification import MapieMultiLabelClassifier
from mapie.regression import (
    MapieQuantileRegressor,
    MapieRegressor,
    MapieTimeSeriesRegressor
)

VALID_MAPIE_ESTIMATORS = {
    "classif_score": {
        "estimator": MapieClassifier,
        "task": "classification",
        "kwargs": {"method": "score"}
    },
    "classif_lac": {
        "estimator": MapieClassifier,
        "task": "classification",
        "kwargs": {"method": "lac"}
    },
    "classif_aps": {
        "estimator": MapieClassifier,
        "task": "classification",
        "kwargs": {"method": "aps"}
    },
    "classif_cumulated_score": {
        "estimator": MapieClassifier,
        "task": "classification",
        "kwargs": {"method": "cumulated_score"}
    },
    "classif_topk": {
        "estimator": MapieClassifier,
        "task": "classification",
        "kwargs": {"method": "top_k"}
    },
    "classif_lac_conformity": {
        "estimator": MapieClassifier,
        "task": "classification",
        "kwargs": {"conformity_score": LACConformityScore()}
    },
    "classif_aps_conformity": {
        "estimator": MapieClassifier,
        "task": "classification",
        "kwargs": {"conformity_score": APSConformityScore()}
    },
    "classif_topk_conformity": {
        "estimator": MapieClassifier,
        "task": "classification",
        "kwargs": {"conformity_score": TopKConformityScore()}
    },
    "regression_absolute_conformity": {
        "estimator": MapieRegressor,
        "task": "regression",
        "kwargs": {"conformity_score": AbsoluteConformityScore()}
    },
    "regression_gamma_conformity": {
        "estimator": MapieRegressor,
        "task": "regression",
        "kwargs": {"conformity_score": GammaConformityScore()}
    },
}

VALID_MAPIE_ESTIMATORS_NAMES = list(VALID_MAPIE_ESTIMATORS.keys())

NON_VALID_CS = {
    "classif_raps": {
        "estimator": MapieClassifier,
        "task": "classification",
        "kwargs": {"method": "raps"}
    },
    "classif_raps_conformity": {
        "estimator": MapieClassifier,
        "task": "classification",
        "kwargs": {"conformity_score": RAPSConformityScore()}
    },
    "regression_residual_conformity": {
        "estimator": MapieRegressor,
        "task": "regression",
        "kwargs": {"conformity_score": ResidualNormalisedScore()}
    }
}

NON_VALID_CS_NAMES = list(NON_VALID_CS.keys())

NON_VALID_MAPIE_ESTIMATORS = {
    "calibration": {
        "estimator": MapieCalibrator,
        "task": "calibration",
        "kwargs": {"method": "top_label", "random_state": 0}
    },
    "multi_label_recall_crc": {
        "estimator": MapieMultiLabelClassifier,
        "task": "multilabel_classification",
        "kwargs": {"metric_control": "recall", "method": "crc"}
    },
    "multi_label_recall_rcps": {
        "estimator": MapieMultiLabelClassifier,
        "task": "multilabel_classification",
        "kwargs": {"metric_control": "recall", "method": "rcps"},
        "predict_kargs": {"delta": 0.01}
    },
    "multi_label_precision_ltt": {
        "estimator": MapieMultiLabelClassifier,
        "task": "multilabel_classification",
        "kwargs": {"metric_control": "precision", "method": "ltt"},
        "predict_kargs": {"delta": 0.01}
    },
    "mapie_quantile": {
        "estimator": MapieQuantileRegressor,
        "task": "regression",
        "kwargs": {"method": "quantile"}
    },
    "mapie_time_series": {
        "estimator": MapieTimeSeriesRegressor,
        "task": "regression",
        "kwargs": {"method": "quantile"}
    }
}

NON_VALID_MAPIE_ESTIMATORS_NAMES = list(NON_VALID_MAPIE_ESTIMATORS.keys())

TOY_DATASETS = {
    "calibration": make_classification(
        n_samples=1000, n_features=5, n_informative=5,
        n_redundant=0, n_classes=10
    ),
    "classification": make_classification(
        n_samples=1000, n_features=5, n_informative=5,
        n_redundant=0, n_classes=10
    ),
    "multilabel_classification": make_multilabel_classification(
        n_samples=1000, n_features=5, n_classes=5, allow_unlabeled=False
    ),
    "regression": make_regression(
        n_samples=1000, n_features=5, n_informative=5
    )

}

ML_MODELS = {
    "calibration": LogisticRegression(),
    "classification": LogisticRegression(),
    "multilabel_classification": MultiOutputClassifier(
                LogisticRegression(multi_class="multinomial")
            ),
    "regression": LinearRegression(),
}


@pytest.mark.parametrize("mapie_estimator_name", VALID_MAPIE_ESTIMATORS_NAMES)
def test_valid_estimators_dont_fail(mapie_estimator_name):
    """
    Test that valid estimators don't fail"""
    task_dict = VALID_MAPIE_ESTIMATORS[mapie_estimator_name]
    mapie_estimator = task_dict["estimator"]
    mapie_kwargs = task_dict["kwargs"]
    task = task_dict["task"]
    x, y = TOY_DATASETS[task]
    y = np.abs(y)  # to avoid negative values with Gamma NCS
    ml_model = ML_MODELS[task]
    groups = np.random.choice(10, len(x))
    model = clone(ml_model)
    model.fit(x, y)
    mapie_inst = deepcopy(mapie_estimator)
    if task not in ["multilabel_classification", "calibration"]:
        mondrian_cp = MondrianCP(
            mapie_estimator=mapie_inst(
                estimator=model, cv="prefit", **mapie_kwargs
            )
        )
    elif task == "multilabel_classification":
        mondrian_cp = MondrianCP(
            mapie_estimator=mapie_inst(estimator=model, **mapie_kwargs),
        )
    else:
        mondrian_cp = MondrianCP(
            mapie_estimator=mapie_inst(estimator=model, cv="prefit")
        )
    if task == "multilabel_classification":
        mondrian_cp.fit(x, y, groups=groups)
        if mapie_estimator_name in [
            "multi_label_recall_rcps", "multi_label_precision_ltt"
        ]:
            mondrian_cp.predict(
                x, groups=groups, alpha=.2, **task_dict["predict_kargs"]
            )
        else:
            mondrian_cp.predict(x, groups=groups, alpha=.2)
    elif task == "calibration":
        mondrian_cp.fit(x, y, groups=groups, **mapie_kwargs)
        mondrian_cp.predict_proba(x, groups=groups)
    else:
        mondrian_cp.fit(x, y, groups=groups, **mapie_kwargs)
        mondrian_cp.predict(x, groups=groups, alpha=.2)


@pytest.mark.parametrize(
        "mapie_estimator_name", NON_VALID_CS_NAMES
)
def test_non_cs_fails(mapie_estimator_name):
    """
    Test that non valid conformity scores fail"""
    task_dict = NON_VALID_CS[mapie_estimator_name]
    mapie_estimator = task_dict["estimator"]
    mapie_kwargs = task_dict["kwargs"]
    task = task_dict["task"]
    x, y = TOY_DATASETS[task]
    ml_model = ML_MODELS[task]
    groups = np.random.choice(10, len(x))
    model = clone(ml_model)
    model.fit(x, y)
    mapie_inst = deepcopy(mapie_estimator)
    mondrian_cp = MondrianCP(
        mapie_estimator=mapie_inst(
            estimator=model, cv="prefit", **mapie_kwargs
        )
    )
    with pytest.raises(ValueError, match=r".*The conformity score for*"):
        mondrian_cp.fit(x, y, groups=groups)


@pytest.mark.parametrize("mapie_estimator_name", VALID_MAPIE_ESTIMATORS_NAMES)
@pytest.mark.parametrize("non_valid_cv", ["split", -1, 5, ShuffleSplit(1)])
def test_invalid_cv_fails(mapie_estimator_name, non_valid_cv):
    """
    Test that invalid cv fails"""
    task_dict = VALID_MAPIE_ESTIMATORS[mapie_estimator_name]
    mapie_estimator = task_dict["estimator"]
    mapie_kwargs = task_dict["kwargs"]
    task = task_dict["task"]
    x, y = TOY_DATASETS[task]
    ml_model = ML_MODELS[task]
    groups = np.random.choice(10, len(x))
    model = clone(ml_model)
    mapie_inst = deepcopy(mapie_estimator)
    if not isinstance(mapie_inst(), MapieMultiLabelClassifier):
        mondrian_cp = MondrianCP(
            mapie_estimator=mapie_inst(estimator=model, cv=non_valid_cv)
        )
    else:
        mondrian_cp = MondrianCP(
            mapie_estimator=mapie_inst(estimator=model, **mapie_kwargs),
        )
    if task == "multilabel_classification":
        with pytest.raises(
            ValueError, match=r".*MultiOutputClassifier instance is not*"
        ):
            mondrian_cp.fit(x, y, groups=groups)
    elif task == "calibration":
        with pytest.raises(ValueError, match=r".*estimator uses cv='prefit'*"):
            mondrian_cp.fit(x, y, groups=groups, **mapie_kwargs)
    else:
        with pytest.raises(ValueError, match=r".*estimator uses cv='prefit'*"):
            mondrian_cp.fit(x, y, groups=groups, **mapie_kwargs)


@pytest.mark.parametrize(
        "mapie_estimator_name", NON_VALID_MAPIE_ESTIMATORS_NAMES
)
def test_non_valid_estimators_fails(mapie_estimator_name):
    """
    Test that valid estimators don't fail"""
    task_dict = NON_VALID_MAPIE_ESTIMATORS[mapie_estimator_name]
    mapie_estimator = task_dict["estimator"]
    mapie_kwargs = task_dict["kwargs"]
    task = task_dict["task"]
    x, y = TOY_DATASETS[task]
    y = np.abs(y)  # to avoid negative values with Gamma NCS
    ml_model = ML_MODELS[task]
    groups = np.random.choice(10, len(x))
    model = clone(ml_model)
    model.fit(x, y)
    mapie_inst = deepcopy(mapie_estimator)
    if task not in ["multilabel_classification", "calibration"]:
        mondrian_cp = MondrianCP(
            mapie_estimator=mapie_inst(
                estimator=model, cv="prefit", **mapie_kwargs
            )
        )
    elif task == "multilabel_classification":
        mondrian_cp = MondrianCP(
            mapie_estimator=mapie_inst(estimator=model, **mapie_kwargs),
        )
    else:
        mondrian_cp = MondrianCP(
            mapie_estimator=mapie_inst(estimator=model, cv="prefit")
        )
    with pytest.raises(ValueError, match=r".*The estimator must be a*"):
        if task == "multilabel_classification":
            mondrian_cp.fit(x, y, groups=groups)
        elif task == "calibration":
            mondrian_cp.fit(x, y, groups=groups, **mapie_kwargs)
        else:
            mondrian_cp.fit(x, y, groups=groups, **mapie_kwargs)


def test_groups_not_defined_by_integers_fails():
    """
    Test that groups not defined by integers fails"""
    x, y = TOY_DATASETS["classification"]
    ml_model = ML_MODELS["classification"]
    model = clone(ml_model)
    model.fit(x, y)
    mondrian = MondrianCP(
        mapie_estimator=MapieClassifier(estimator=model, cv="prefit")
    )
    groups = np.random.choice(10, len(x)).astype(str)
    with pytest.raises(
        ValueError, match=r".*The groups must be defined by integers*"
    ):
        mondrian.fit(x, y, groups=groups)


def test_groups_with_less_than_2_fails():
    """
    Test that groups with less than 2 elements fails"""
    x, y = TOY_DATASETS["classification"]
    ml_model = ML_MODELS["classification"]
    model = clone(ml_model)
    model.fit(x, y)
    mondrian = MondrianCP(
        mapie_estimator=MapieClassifier(estimator=model, cv="prefit")
    )
    groups = np.array([1] + [2] * (len(x) - 1))
    with pytest.raises(
        ValueError, match=r".*There must be at least 2 individuals*"
    ):
        mondrian.fit(x, y, groups=groups)


def test_groups_and_x_have_same_length_in_fit():
    """
    Test that groups and x have the same length in fit"""
    x, y = TOY_DATASETS["classification"]
    ml_model = ML_MODELS["classification"]
    model = clone(ml_model)
    model.fit(x, y)
    mondrian = MondrianCP(
        mapie_estimator=MapieClassifier(estimator=model, cv="prefit")
    )
    groups = np.random.choice(10, len(x) - 1)
    with pytest.raises(ValueError, match=r".*he number of individuals in*"):
        mondrian.fit(x, y, groups=groups)


def test_all_groups_in_predict_are_in_fit():
    """
    Test that all groups in predict are in fit"""
    x, y = TOY_DATASETS["classification"]
    ml_model = ML_MODELS["classification"]
    model = clone(ml_model)
    model.fit(x, y)
    mondrian = MondrianCP(
        mapie_estimator=MapieClassifier(estimator=model, cv="prefit")
    )
    groups = np.random.choice(10, len(x))
    mondrian.fit(x, y, groups=groups)
    groups = np.array([99] * len(x))
    with pytest.raises(ValueError, match=r".*There is at least one new*"):
        mondrian.predict(x, groups=groups, alpha=.2)


def test_groups_and_x_have_same_length_in_predict():
    """
    Test that groups and x have the same length in predict"""
    x, y = TOY_DATASETS["classification"]
    ml_model = ML_MODELS["classification"]
    model = clone(ml_model)
    model.fit(x, y)
    mondrian = MondrianCP(
        mapie_estimator=MapieClassifier(estimator=model, cv="prefit")
    )
    groups = np.random.choice(10, len(x))
    mondrian.fit(x, y, groups=groups)
    groups = np.random.choice(10, len(x) - 1)
    with pytest.raises(ValueError, match=r".*The number of individuals in*"):
        mondrian.predict(x, groups=groups, alpha=.2)


def test_alpha_none_return_one_element():
    """
    Test that if alpha is None, the output is a single element"""
    x, y = TOY_DATASETS["classification"]
    ml_model = ML_MODELS["classification"]
    model = clone(ml_model)
    model.fit(x, y)
    mondrian = MondrianCP(
        mapie_estimator=MapieClassifier(estimator=model, cv="prefit")
    )
    groups = np.random.choice(10, len(x))
    mondrian.fit(x, y, groups=groups)
    preds = mondrian.predict(x, groups=groups)
    assert len(preds) == len(x)


def test_groups_is_list_ok():
    """
    Test that the groups can be a list"""
    x, y = TOY_DATASETS["classification"]
    ml_model = ML_MODELS["classification"]
    model = clone(ml_model)
    model.fit(x, y)
    mondrian = MondrianCP(
        mapie_estimator=MapieClassifier(estimator=model, cv="prefit")
    )
    groups = np.random.choice(10, len(x)).tolist()
    mondrian.fit(x, y, groups=groups)
    mondrian.predict(x, groups=groups, alpha=.2)


@pytest.mark.parametrize("mapie_estimator_name", VALID_MAPIE_ESTIMATORS_NAMES)
def test_same_results_if_only_one_group(mapie_estimator_name):
    """
    Test that the results are the same if there is only one group"""
    task_dict = VALID_MAPIE_ESTIMATORS[mapie_estimator_name]
    mapie_estimator = task_dict["estimator"]
    mapie_kwargs = task_dict["kwargs"]
    task = task_dict["task"]
    x, y = TOY_DATASETS[task]
    ml_model = ML_MODELS[task]
    groups = [0] * len(x)
    model = clone(ml_model)
    model.fit(x, y)
    mapie_inst_mondrian = deepcopy(mapie_estimator)
    mapie_classic_inst = deepcopy(mapie_estimator)
    if not isinstance(mapie_inst_mondrian(), MapieMultiLabelClassifier):
        mondrian_cp = MondrianCP(
            mapie_estimator=mapie_inst_mondrian(estimator=model, cv="prefit")
        )
        mapie_classic = mapie_classic_inst(estimator=model, cv="prefit")
    else:
        mondrian_cp = MondrianCP(
            mapie_estimator=mapie_inst_mondrian(
                estimator=model, **mapie_kwargs
            ),
        )
        mapie_classic = mapie_classic_inst(estimator=model, **mapie_kwargs)
    if task == "multilabel_classification":
        mondrian_cp.fit(x, y, groups=groups)
        mapie_classic.fit(x, y)
        if mapie_estimator_name in [
            "multi_label_recall_rcps", "multi_label_precision_ltt"
        ]:
            mondrian_pred = mondrian_cp.predict(
                x, groups=groups, alpha=.2, **task_dict["predict_kargs"]
            )
            classic_pred = mapie_classic.predict(
                x, alpha=.2, **task_dict["predict_kargs"]
            )
        else:
            mondrian_pred = mondrian_cp.predict(x, groups=groups, alpha=.2)
            classic_pred = mapie_classic.predict(x, alpha=.2)

    elif task == "calibration":
        mondrian_cp.fit(X=x, y=y, groups=groups, **mapie_kwargs)
        mapie_classic.fit(x, y, **mapie_kwargs)
        mondrian_pred = mondrian_cp.predict_proba(x, groups=groups)
        classic_pred = mapie_classic.predict_proba(x)
        assert np.allclose(mondrian_pred, classic_pred, equal_nan=True)
    else:
        mondrian_cp.fit(x, y, groups=groups, **mapie_kwargs)
        mapie_classic.fit(x, y, **mapie_kwargs)
        mondrian_pred = mondrian_cp.predict(x, groups=groups, alpha=.2)
        classic_pred = mapie_classic.predict(x, alpha=.2)
        assert np.allclose(mondrian_pred[0], classic_pred[0])
        assert np.allclose(mondrian_pred[1], classic_pred[1])