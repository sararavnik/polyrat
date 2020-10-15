import numpy as np
from .basis import *
from copy import deepcopy
import scipy.linalg
import cvxpy as cp

class Polynomial:
	def __init__(self, basis, coef):
		self.basis = deepcopy(basis)
		self.coef = np.copy(coef)

	def __call__(self, X):
		return self.basis.vandermonde(X) @ self.coef

	def eval(self, X):
		return self.basis.vandermonde(X) @ self.coef

	def roots(self, *args, **kwargs): 
		return self.basis.roots(self.coef, *args, **kwargs)	


def _polynomial_fit_least_squares(P, y):
	coef, _, _, _ = scipy.linalg.lstsq(P, y)
	return coef.flatten()

def _polynomial_fit_pnorm(P, y, norm, **kwargs):
	if np.iscomplexobj(P) or np.iscomplexobj(y):
		a = cp.Variable(P.shape[1], complex = True)
	else:
		a = cp.Variable(P.shape[1], complex = False)
	
	prob = cp.Problem(cp.Minimize(cp.norm(P @ a - y, p = norm)))
	prob.solve(**kwargs)
	return a.value

class PolynomialApproximation(Polynomial):
	def __init__(self, degree, Basis = None, norm = 2):
		assert norm >= 1
		if Basis is None:
			from .arnoldi import ArnoldiPolynomialBasis
			Basis = ArnoldiPolynomialBasis
		self.Basis = Basis
		self.degree = degree
		self.norm = norm

	def fit(self, X, y, **kwargs):
		self.basis = self.Basis(X, self.degree)
		P = self.basis.basis()
		if self.norm == 2 or self.norm == 2.:
			self.coef = _polynomial_fit_least_squares(P, y)
		else:
			self.coef = _polynomial_fit_pnorm(P, y, self.norm, **kwargs)
		


