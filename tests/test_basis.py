import numpy as np
import pytest
from polyrat import *
from scipy.linalg import subspace_angles



@pytest.mark.parametrize("M", [500])
@pytest.mark.parametrize("degree", [0,1,2,5])
@pytest.mark.parametrize("dim", [1,3,5])
@pytest.mark.parametrize("Basis", 
	[MonomialPolynomialBasis,
	 LegendrePolynomialBasis,
	 ChebyshevPolynomialBasis,
	 HermitePolynomialBasis, 
	 LaguerrePolynomialBasis,
	 ArnoldiPolynomialBasis])
@pytest.mark.parametrize("seed", [0])
def test_monomial_total(M, degree, dim, Basis, seed):
	r""" Check that a vector constructed in the monomial basis 
	is in the space generated by the Vandermonde matrix
	"""
	np.random.seed(seed)
	X = np.random.randn(M, dim)
	basis = Basis(X, degree)

	V = basis.basis()
	Q, R = np.linalg.qr(V)

	for idx in total_degree_index(dim, degree):
		y = np.ones(M)
		for j in range(dim):
			y *= X[:,j]**idx[j]
		
		err = y - Q @ Q.T.conj() @ y
		err_norm = np.linalg.norm(err)
		print("idx", idx, "error", err_norm)
		assert err_norm < 5e-9, "Vector not contained in space"

@pytest.mark.parametrize("M", [500])
@pytest.mark.parametrize("degree",[
	(0,),
	(1,),
	(5,),
	(1,1),
	(5,1),
	(0,5,1),
	(5,0,1),
	(2,2,2), 
	])
@pytest.mark.parametrize("Basis", 
	[MonomialPolynomialBasis,
	 LegendrePolynomialBasis,
	 ChebyshevPolynomialBasis,
	 HermitePolynomialBasis, 
	 LaguerrePolynomialBasis,
	 ArnoldiPolynomialBasis])
@pytest.mark.parametrize("seed", [0])
def test_monomial_max(M, degree, Basis, seed):
	np.random.seed(seed)
	X = np.random.randn(M, len(degree))
	basis = Basis(X, degree)

	V = basis.basis()
	Q, R = np.linalg.qr(V)

	for idx in max_degree_index(degree):
		y = np.ones(M)
		for j in range(len(degree)):
			y *= X[:,j]**idx[j]
		
		err = y - Q @ Q.T.conj() @ y
		err_norm = np.linalg.norm(err)
		print("idx", idx, "error", err_norm)
		assert err_norm < 1e-8, "Vector not contained in space"


@pytest.mark.parametrize("n_grid", [10])
@pytest.mark.parametrize("degree",[
	5,
	(7,2),
	(2,7),
	(3,0,4)
	])
@pytest.mark.parametrize("dim", [1,2,3])
@pytest.mark.parametrize("Basis", 
	[MonomialPolynomialBasis,
	 ChebyshevPolynomialBasis,
	 HermitePolynomialBasis, 
	 LaguerrePolynomialBasis,
	 ArnoldiPolynomialBasis])
def test_subspace_angles_basis(n_grid, degree, dim,  Basis):

	# Exit without error if testing a total degree problem
	try:
		degree = int(degree)
	except (TypeError, ValueError):
		if len(degree) != dim: return

	# Construct grid 
	Xs = np.meshgrid(*[np.linspace(-1,1,n_grid) for i in range(dim)])
	X = np.vstack([Xi.flatten() for Xi in Xs]).T
	
	
	# We use Legendre polynomials as a reference solution
	leg = LegendrePolynomialBasis(X, degree)
	basis = Basis(X, degree)
	
	V1 = leg.basis()
	V2 = basis.basis()

	tol = 1e-10
	# This Laguerre polynomials are not particularly well conditioned
	if Basis is LaguerrePolynomialBasis: tol = 1e-7

	for k in range(1,V1.shape[1]):
		ang = subspace_angles(V1[:,:k], V2[:,:k])
		print(basis._indices[k], np.max(ang))
		assert np.max(ang) < tol



@pytest.mark.parametrize("seed", [0])
@pytest.mark.parametrize("degree",[
	5,
	(7,2),
	(2,7),
	(3,0,4)
	])
@pytest.mark.parametrize("dim", [1,2,3])
@pytest.mark.parametrize("Basis", 
	[MonomialPolynomialBasis,
	 ChebyshevPolynomialBasis,
	 HermitePolynomialBasis, 
	 LaguerrePolynomialBasis,
	 ArnoldiPolynomialBasis])
def test_subspace_angles(seed, degree, dim,  Basis):

	# Exit without error if testing a total degree problem
	try:
		degree = int(degree)
	except (TypeError, ValueError):
		if len(degree) != dim: return

	# Construct grid 
	X = np.random.randn(500, dim)

	X2 = np.random.randn(200, dim)	
	# We use Legendre polynomials as a reference solution
	leg = LegendrePolynomialBasis(X, degree)
	basis = Basis(X, degree)
	
	V1 = leg.vandermonde(X2)
	V2 = basis.vandermonde(X2)

	tol = 1e-10
	# This Laguerre polynomials are not particularly well conditioned
	if Basis is LaguerrePolynomialBasis: tol = 1e-7

	for k in range(1,V1.shape[1]):
		ang = subspace_angles(V1[:,:k], V2[:,:k])
		print(basis._indices[k], np.max(ang))
		assert np.max(ang) < tol


@pytest.mark.parametrize("Basis", 
	[MonomialPolynomialBasis,
	 LegendrePolynomialBasis,
	 ChebyshevPolynomialBasis,
	 HermitePolynomialBasis, 
	 LaguerrePolynomialBasis])
@pytest.mark.parametrize("dim", [1,2,3])
def test_scale(Basis, dim):
	X = np.random.randn(1000, dim)
	basis = Basis(X, 2)
	Y = basis._scale(X)
	Z = basis._inv_scale(Y)
	err = np.linalg.norm(Z - X, np.inf)
	print("error", err)
	assert err < 1e-10, "Scaling/inverse scaling does not map to identity"



@pytest.mark.parametrize("Basis",
	[MonomialPolynomialBasis,
	 LegendrePolynomialBasis,
	 ChebyshevPolynomialBasis,
	 HermitePolynomialBasis, 
	 LaguerrePolynomialBasis,
	ArnoldiPolynomialBasis,
	]
)
@pytest.mark.parametrize("dim", [1,2,3])
@pytest.mark.parametrize("degree",
	[3,
	(3,2),
	(2,3),
	(3,0,2),
	]
)
def test_vandermonde_derivative(Basis, dim, degree):
	
	# Exit without error if testing a total degree problem
	try:
		degree = int(degree)
	except (TypeError, ValueError):
		if len(degree) != dim: return

	np.random.seed(0)
	X = np.random.randn(1000, dim) 
	#X = np.linspace(-2,2, 100).reshape(-1,1)
	basis = Basis(X, degree)

	X = np.random.randn(100, dim)
	#X = np.linspace(-1, 1, 11).reshape(-1,1)
	V = basis.vandermonde(X)
	DV = basis.vandermonde_derivative(X)
	for k in range(dim):
		tau = 1e-7
		dX = np.zeros_like(X)
		dX[:,k] = tau
		dV = basis.vandermonde(X + dX)
		DV_est = (dV - V)/tau
		err = DV[:,:,k]  - DV_est
		norm_err = np.linalg.norm(err)
		print(f"err {norm_err:10.6e}")
		if Basis == HermitePolynomialBasis:
			assert norm_err < 5e-5
		else:
			assert norm_err < 1e-6

if __name__ == '__main__':
	#test_monomial_total(100, 10, 3, MonomialPolynomialBasis,0) 
	#test_monomial_max(100, [4], MonomialPolynomialBasis,0) 
	#test_subspace_angles(10, [1,4], 2, ArnoldiPolynomialBasis)
	#test_scale(MonomialPolynomialBasis, 1)
	test_vandermonde_derivative(ArnoldiPolynomialBasis, 2, (3,2))
	pass



