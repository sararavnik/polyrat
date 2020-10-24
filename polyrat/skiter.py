""" Routines implementing variants of the Sanathanan-Koerner iteration
"""
import numpy as np
from numpy.linalg import LinAlgError
import scipy.linalg
import scipy.optimize
from .basis import *
from .arnoldi import *
from .polynomial import *
from iterprinter import IterationPrinter



def _minimize_2_norm(A):
	r"""
		Solve the optimization problem 
		
		min_x  || A @ x ||_2
	"""
	U, s, VH = scipy.linalg.svd(A, full_matrices = False)
		
	# Condition number of singular vectors, cf. Stewart 01: Eq. 3.16
	with np.errstate(divide = 'ignore'):
		cond = s[0]*np.sqrt(2)/(s[-2] - s[-1])
	return VH.T.conj()[:,-1], cond


def _minimize_inf_norm(A, nsamp = 360):
	r"""

	min_x || A @ x ||_inf s.t. ||x||_2 = 1

	If A is real, then x is real

	"""

	if np.all(np.isreal(A)):
		return _minimize_inf_norm_real(A)
	else:
		return _minimize_inf_norm_complex(A, nsamp = nsamp)


def _minimize_inf_norm_real(A):
	m,n = A.shape
	A_ub = np.vstack([ 
		# A @ x - t <= 0
		np.hstack([A, -np.ones((m,1))]),
		# -A @ x - t <= 0
		np.hstack([-A, -np.ones((m,1))]),
		])
	b_ub = np.zeros(2*m)
	
	c = np.zeros(n + 1)
	c[-1] = 1.
	bounds = np.zeros((n+1, 2))
	bounds[:n,0] = -np.inf
	bounds[:,1] = np.inf
	
	x, cond = _minimize_2_norm(A) 
	A_eq = np.zeros((1,n+1))
	A_eq[0,:n] = x.real
	b_eq = np.ones((1,))

	res = scipy.optimize.linprog(c, A_ub = A_ub, b_ub = b_ub, A_eq = A_eq, b_eq = b_eq, bounds = bounds,
		options = {'cholesky': False, 'sym_pos':False, 'lstsq': True})
	x = res.x[:-1]
	return x/np.linalg.norm(x), cond

def _minimize_inf_norm_complex(A, nsamp = 360):
	m, n = A.shape
	A_ub = [
		# Ar @ xr - Ai @ xi - tr <=0 
		np.hstack([A.real, -A.imag, -np.ones((m, 1)), np.zeros((m, 1)), np.zeros((m,1)) ]),
		# Ai @ xr + Ar @ xi - ti <=0 
		np.hstack([A.real, A.imag, np.zeros((m, 1)), -np.ones((m, 1)), np.zeros((m,1)) ]),
		# -Ar @ xr + Ai @ xi - tr <=0 
		np.hstack([-A.real, A.imag, -np.ones((m, 1)), np.zeros((m, 1)), np.zeros((m,1)) ]),
		# -Ai @ xr - Ar @ xi - ti <=0 
		np.hstack([-A.real, -A.imag, np.zeros((m, 1)), -np.ones((m, 1)), np.zeros((m,1)) ]),
		]
	# constraints on tr + ti
	th = np.linspace(0, 2*np.pi, nsamp, endpoint = False)
	A_ub.append(
		np.hstack( [np.zeros((nsamp, 2*n)), np.cos(th).reshape(-1,1), np.sin(th).reshape(-1,1), -np.ones((nsamp,1))])
		)
	A_ub = np.vstack(A_ub)

	b_ub = np.zeros(A_ub.shape[0])
	
	c = np.zeros(2*n + 3)
	c[-1] = 1.
	
	bounds = np.zeros((2*n+3, 2))
	bounds[:2*n,0] = -np.inf
	bounds[:,1] = np.inf


	x, cond = _minimize_2_norm(A) 
	A_eq = np.hstack([x.real, x.imag, np.zeros(3)]).reshape(1,-1)
	b_eq = np.ones((1,))

	res = scipy.optimize.linprog(c, A_ub = A_ub, b_ub = b_ub, A_eq = A_eq, b_eq = b_eq, bounds = bounds,
		options = {'cholesky': False, 'sym_pos':False, 'lstsq': True})
	
	x = res.x[:n] + 1j*res.x[n:2*n]
	
	return x/np.linalg.norm(x), cond


def _minimize_1_norm(A):
	raise NotImplementedError


#def _minimize_1_norm_real(A):
#	r"""
#		Solve the optimization problem 
#		
#		min_x  || A @ x ||_1  s.t.  ||x||_2 = 1
#	"""
#	m, n = A.shape
#
#	U, s, VH = np.linalg.svd(A, full_matrices = False)
#	print(m,n, *U.shape)
#	A_ub = np.vstack([
#			# A x - t <= 0
#			np.hstack([A, -np.eye(m)]),
#			# -A x - t <= 0 
#			np.hstack([-A, -np.eye(m)])
#			])
#	b_ub = np.zeros(2*m)
#
#	# Pin one of the variables so we have a non-zero solution
#	A_eq = np.zeros((1, m +n))
#	A_eq[0,0] = 1
#	b_eq = np.ones((1,))
#
#	# Objective: minimize the sum of the upper bounds
#	c = np.zeros(n + m)
#	c[n:] = 1.
#
#	lb = -np.inf*np.ones(m+n)
#	ub = np.inf*np.ones(m+n)
#	lb[n:] = 0
#	
#	bounds = [[None, None] for i in range(m+n)]
#	for i in range(m): bounds[n+i][0] = 0
#
#	res = scipy.optimize.linprog(c, A_ub = A_ub, b_ub = b_ub, A_eq = A_eq, b_eq = b_eq, bounds = bounds,
#			options = {'presolve': True, 'autoscale': True, 'lstsq': True})
#	
#	#y = res.x[:n]
#	# U @ y = A @ x 
#	# U @ y = U @ np.diag(s) @ VH @ x
#	# y = np.diag(s) @ VH @ x
#	#x = (VH.conj().T @ (y/s ))
#	x = res.x[:n]
#	x /= np.linalg.norm(x)
#	x *= np.sign(x[0])
#	return x, s
		


def skfit(y, P, Q, maxiter = 20, verbose = True, history = False, denom0 = None, norm = 2, xtol = 1e-7):
	r"""


	Returns
	-------
	a: np.array 
		Numerator coefficients
	b: np.array
		Denominator coefficients
	"""	
	if denom0 is None:
		denom = np.ones(len(y), dtype = y.dtype)
	else:
		assert len(denom0) == len(y)
		denom = np.array(denom0)
	
	if np.isclose(norm, 2):
		linearized_solution = _minimize_2_norm
	elif ~np.isfinite(norm):
		linearized_solution = _minimize_inf_norm
	else: 
		raise NotImplementedError

	if verbose:
		printer = IterationPrinter(it = '4d', res_norm = '21.15e', delta_fit = '8.2e', cond = '8.2e')
		printer.print_header(it = 'iter', res_norm = 'residual norm', delta_fit = 'delta fit', cond = 'cond')
	
	if history:
		hist = []

	# As there are no guarntees about convergence,
	# we record the best iteration
	best_res_norm = np.inf
	best_sol = None	
	
	# For comparison with current iterate to determine termination
	fit_old = np.zeros(y.shape[0], dtype = y.dtype)

	
	for it in range(maxiter):
		A = np.hstack([ 
				np.multiply((1./denom)[:,None], P), 	
				np.multiply((-y/denom)[:,None], Q)
			])

		x, cond = linearized_solution(A)
		
		a = x[:P.shape[1]]
		b = x[-Q.shape[1]:]
		Pa = P @ a
		Qb = Q @ b
		fit = Pa/Qb
		res_norm = np.linalg.norm(y - fit, norm)

		if res_norm < best_res_norm:
			best_res_norm = res_norm
			best_sol = [a, b]

		delta_fit = np.linalg.norm(fit - fit_old, norm)		
		
		if history:
			hist.append({'fit': fit, 'cond': cond})

		if verbose:
			printer.print_iter(it = it, delta_fit = delta_fit, res_norm = res_norm, cond = cond) 

		if delta_fit < xtol:
			break

		# Copy over data for next loop
		denom = Qb 
		fit_old = fit

	if history:	
		return best_sol + [hist]
	else:
		return best_sol



def skfit_rebase(X, y, num_degree, denom_degree, maxiter = 20, verbose = True, 
	xtol = 1e-7, history = False, denom0 = None, norm = 2):
	r""" The SK-iteration, but at each step use Vandermonde with Arnoldi to construct a new basis

	Parameters
	----------
	X: np.array (M,dim)
		
	y: np.array (M,)


	Returns
	-------
			
	"""

	if history:
		hist = []


	if denom0 is None:
		denom = np.ones(X.shape[0], dtype = X.dtype)
	else:
		assert denom0.shape[0] == X.shape[0]
		denom = denom0


	if np.isclose(norm, 2):
		linearized_solution = _minimize_2_norm
	elif ~np.isfinite(norm):
		linearized_solution = _minimize_inf_norm
	else: 
		raise NotImplementedError
	
	if verbose:
		printer = IterationPrinter(it = '4d', res_norm = '21.15e', delta_fit = '8.2e', cond = '8.2e')
		printer.print_header(it = 'iter', res_norm = 'residual norm', delta_fit = 'delta fit', cond = 'cond')

	# As there are no guarntees about convergence,
	# we record the best iteration
	best_res_norm = np.inf
	best_sol = None	
	
	# For comparison with current iterate to determine termination
	fit_old = np.zeros(y.shape[0], dtype = X.dtype)

	for it in range(maxiter):
		try:
			num_basis = ArnoldiPolynomialBasis(X, num_degree, weight = 1./denom)
			denom_basis = ArnoldiPolynomialBasis(X, denom_degree, weight = 1./denom)
			P = num_basis.basis()
			Q = denom_basis.basis()	
			#P, RP, _ = vandermonde_arnoldi_CGS(X, num_degree, weight = 1./denom)	
			#Q, RQ, _ = vandermonde_arnoldi_CGS(X, denom_degree, weight = 1./denom)	
			
			A = np.hstack([P, np.multiply(-y[:,None], Q) ])
			x, cond = linearized_solution(A)
			a = x[:P.shape[1]]
			b = x[-Q.shape[1]:]
			
			Pa = P @ a
			Qb = Q @ b

			fit = Pa/Qb

			delta_fit = np.linalg.norm(fit - fit_old, norm)		
			res_norm = np.linalg.norm(fit - y, norm)
		
		except (LinAlgError, ValueError) as e:
			if verbose: print(e)
			break
	

		# If we have improved the fit, append this 
		if res_norm < best_res_norm:
			numerator = Polynomial(num_basis, a)
			denominator = Polynomial(denom_basis, b)
			best_sol = [numerator, denominator]
			best_res_norm = res_norm

		if history:
			hist.append({'fit': fit, 'cond':cond})

		if verbose:
			printer.print_iter(it = it, delta_fit = delta_fit, res_norm = res_norm, cond = cond) 

		if delta_fit < xtol:
			break

		denom = np.abs(denom * Qb)
		denom[denom == 0.] = 1.
		fit_old = fit

	if history:	
		return best_sol + [hist]
	else:
		return best_sol
