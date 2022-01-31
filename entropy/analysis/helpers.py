"""
Analysis helper functions.

"""

import linearmodels as lm


def fe_reg(y, x, entity_effects, time_effects):
    return lm.PanelOLS(
        y,
        x,
        entity_effects=entity_effects,
        time_effects=time_effects,
    ).fit(cov_type="clustered", cluster_entity=True)
