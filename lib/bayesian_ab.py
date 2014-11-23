import numpy as np
from scipy.stats import beta as beta_dist


def calculate_posteriors(installs_A, installs_B, views_A, views_B):
    # Prior Parameters
    alpha = .5
    beta = 100

    # Update Equations
    alpha_post_A, beta_post_A = installs_A + alpha, beta + views_A - installs_A
    alpha_post_B, beta_post_B = installs_B + alpha, beta + views_B - installs_B

    # Draw samples from posteriors
    posterior_A = beta_dist(a=alpha_post_A, b=beta_post_A)
    posterior_B = beta_dist(a=alpha_post_B, b=beta_post_B)

    return posterior_A, posterior_B


def get_samples(posterior, size=1000000):
    return posterior.rvs(size)


def get_prob_better(a_samps, b_samps):
    '''
    Returns Probability B > A
    '''
    return np.mean(b_samps > a_samps)


def get_prob_X_better(a_samps, b_samps, SENSITIVITY):
    '''
    Returns Probability B is X percent better than A, where X is SENSITIVITY
    '''
    percent_better = _gen_lift_vector(a_samps, b_samps)
    return np.mean(percent_better >= SENSITIVITY)


def _gen_lift_vector(a_samps, b_samps):
    lift_vector = (b_samps / a_samps) - 1.0
    lift_vector = lift_vector[a_samps != 0]
    return lift_vector


def get_expected_lift(a_samps, b_samps):
    return np.mean(_gen_lift_vector(a_samps, b_samps))


def get_lift_ci(a_samps, b_samps, coverage=95):
    percentiles = [(100.0 - coverage) / 2.0, coverage + (100.0 - coverage) / 2.0]
    return np.percentile(_gen_lift_vector(a_samps, b_samps), percentiles)