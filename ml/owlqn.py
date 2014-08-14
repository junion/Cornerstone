"""
    SciPy routine (not currently part of SciPy distributions).

    An implementation of the orthant-wise limited memory quasi-Newton algorithm
    for optimizing convex l1-regularized objectives proposed by Galen Andrew and 
    Jianfeng Gao in "Scalable training of l1-regularized log-linear models", ICML 2007. 
    A C++ implementation by the authors is also available. Present implementation 
    closely follows naming and stylistic conventions of SciPy and can be pasted
    into optimize.py. Both scalar and weighted (vector) regularizer trade-offs are
    supported.

    Michael Subotin, msubotin@umiacs.umd.edu, January 2008."""

__all__ = ['fmin_owlqn']

import sys
import numpy
from numpy import atleast_1d, eye, mgrid, argmin, zeros, shape, \
     squeeze, isscalar, vectorize, asarray, absolute, sqrt, Inf, asfarray
from scipy import optimize 

# Start of code copied from optimize.py
# ------------------------------------------------------------
# To make integration of this routine into optimize.py easier,
# the following section has been copied verbatim from it.

def max(m,axis=0):
    """max(m,axis=0) returns the maximum of m along dimension axis.
    """
    m = asarray(m)
    return numpy.maximum.reduce(m,axis)

def min(m,axis=0):
    """min(m,axis=0) returns the minimum of m along dimension axis.
    """
    m = asarray(m)
    return numpy.minimum.reduce(m,axis)

abs = absolute
import __builtin__
pymin = __builtin__.min
pymax = __builtin__.max
__version__="0.7"
_epsilon = sqrt(numpy.finfo(float).eps)

def vecnorm(x, ord=2):
    if ord == Inf:
        return numpy.amax(abs(x))
    elif ord == -Inf:
        return numpy.amin(abs(x))
    else:
        return numpy.sum(abs(x)**ord,axis=0)**(1.0/ord)

def wrap_function(function, args):
    ncalls = [0]
    def function_wrapper(x):
        ncalls[0] += 1
        return function(x, **args)
    return ncalls, function_wrapper


# ------------------------------------------------------------
# End of code copied from optimize.py

def simple_line_search_owlqn(f, old_fval, xk, pk, gfk, k, Cvec):
    """Backtracking line search for fmin_owlqn. A simple line search works reasonably
    well because the search direction has been rescaled so that the Wolfe conditions
    will usually be satisfied for alpha=1 (see Nocedal & Wright, 2006, Numerical
    Optimization, p. 178). NB: To improve efficiency this routine checks only one of
    the Wolfe conditions. This is appropriate only for convex objectives. If the
    objective is not convex it may lead to non-positive-definite Hessian approximations
    and non-descent search directions. (see Nocedal & Wright 2006, chapters 3 and 6.)
    """
    dirDeriv = numpy.dot(pk,gfk)
    if dirDeriv >= 0:
        sys.stderr.write("Warning: Non-descent direction. Check your gradient.\n")
        return None, None, None
    alpha = 1.0
    backoff = 0.5
    if k == 0:
        alpha = 1.0 / (numpy.dot(pk,pk))**(0.5)
        backoff = 0.1
    elif numpy.array_equal(-pk,gfk):
        print '#########'
        print 'HIT!!!!!'
        print '#########'
        alpha = 1.0 * (numpy.dot(xk,xk))**(0.5) / (numpy.dot(pk,pk))**(0.5)
        backoff = 0.1
    c1 = 1e-4
    new_fval = None
    while True:
        new_x = xk + alpha * pk
        crossed_discont = numpy.where(numpy.logical_and(Cvec>0, xk*new_x<0))[0]
        new_x[crossed_discont] = 0
        new_fval = f(new_x) + numpy.dot(Cvec,numpy.absolute(new_x))
        if new_fval <= old_fval + c1 * dirDeriv * alpha:
            break
        alpha *= backoff
        if alpha <= 1e-4:
            return None, None, None
    return alpha, new_fval, new_x

def subgrad(x, gf, Cvec):
    """Subgradient computation for fmin_owlqn."""
    for i in numpy.where(Cvec>0)[0]:
        if x[i] < 0:
            gf[i] -= Cvec[i]
        elif x[i] > 0:
            gf[i] += Cvec[i]
        else:
            if gf[i] < -Cvec[i]:
                gf[i] += Cvec[i]
            elif gf[i] > Cvec[i]:
                gf[i] -= Cvec[i]
            else:
                gf[i] = 0
    return gf

def fmin_owlqn(f, x0, fprime=None, args={}, gtol=1e-5, ftol=1e-4, norm=Inf,
              epsilon=_epsilon, maxiter=None, full_output=0, disp=1,
              retall=0, callback=None, cache_size=10, C=None, Cvec=None):
    """Minimize an l1-regularized convex function using the orthant-wise 
       limited-memory quasi-Netwon algorithm by Andrew & Gao.

    Description:

      Optimize the function, f, whose gradient is given by fprime using the
      orthant-wise limited-memory quasi-Newton method of Andrew & Gao.
      See Galen Andrew & Jianfeng Gao, "Scalable training of l1-regularized
      log-linear models" in proc. 2007 International Conference on Machine Learning.
      For details of underlying L-BFGS computations of search directions see
      Nocedal & Wright 2006, Numerical Optimization, p. 176. NB: to optimize
      non-convex functions the line search has to be changed to check both 
      Wolfe conditions (see Nocedal & Wright 2006, chapters 3 and 6).

    Inputs:

      f -- the Python function or method to be minimized.
      x0 -- the initial guess for the minimizer.

      fprime -- a function to compute the gradient of f.
      args -- extra arguments to f and fprime.
      gtol -- gradient norm must be less than gtol before succesful termination
            (NB: gradient norm will decrease slower than for smooth objectives)
      ftol -- stop if average function change over the course of 10 previous
                iterations is less than ftol 
      norm -- order of norm (Inf is max, -Inf is min)
      epsilon -- if fprime is approximated use this value for
                 the step size (can be scalar or vector)
      callback -- an optional user-supplied function to call after each
                  iteration.  It is called as callback(xk), where xk is the
                  current parameter vector.
      cache_size -- the number of vectors used for L-BFGS approximations.
      C -- scalar defining a simple regularization trade-off.
      Cvec -- vector defining a weighted regularization trade-off.

    Outputs: (xopt, {fopt, gopt, Hopt, func_calls, grad_calls, warnflag}, <allvecs>)

      xopt -- the minimizer of f.

      fopt -- the value of f(xopt).
      gopt -- the value of f'(xopt).  (Should be near 0)
      Bopt -- the value of 1/f''(xopt).  (inverse hessian matrix)
      func_calls -- the number of function_calls.
      grad_calls -- the number of gradient calls.
      warnflag -- an integer warning flag:
                  1 : 'Maximum number of iterations exceeded.'
                  2 : 'Gradient and/or function calls not changing'
      allvecs  --  a list of all iterates  (only returned if retall==1)

    Additional Inputs:

      maxiter -- the maximum number of iterations.
      full_output -- if non-zero then return fopt, func_calls, grad_calls,
                     and warnflag in addition to xopt.
      disp -- print convergence message if non-zero.
      retall -- return a list of results at each iteration if non-zero
    """

    x0 = asarray(x0)
    if Cvec is None:
        if C is None:
            Cvec = numpy.zeros(len(x0), float)
        else:
            Cvec = numpy.array([C]*len(x0), float)
    if maxiter is None:
        maxiter = len(x0)*200
    fval_cache_size = 10 # for stopping criterion
    func_calls, f = wrap_function(f, args)
    if fprime is None:
        grad_calls, myfprime = wrap_function(approx_fprime, (f, epsilon))
    else:
        grad_calls, myfprime = wrap_function(fprime, args)
    gfk = myfprime(x0)
    old_fval = f(x0) + numpy.dot(Cvec, numpy.absolute(x0))
    fvalList = [old_fval]
    xk = x0
    # find penalized subgradients
    gfk = subgrad(xk,gfk,Cvec)
    k = 0
    if retall:
        allvecs = [x0]
    N = len(x0)
    sk = [2*gtol]
    warnflag = 0
    gnorm = vecnorm(gfk,ord=norm)
    sList, yList, rhoList = [], [], []
    while (gnorm > gtol) and (k < maxiter):
        # find search direction (Nocedal & Wright 2006, p.178, Algorithm 7.4)
        q = numpy.array(gfk, dtype=gfk.dtype)
        size = len(sList)
        aList = [None]*size
        if size > 0:
            for i in xrange(size-1,-1,-1):
                aList[i] = rhoList[i] * numpy.dot(sList[i],q)
                q -= aList[i] * yList[i]
            # modify to ensure a well-scaled search direction (N&W 2006, eq. 7.20)
            q *= (rhoList[-1] * numpy.dot(yList[-1],yList[-1]))**(-1)
            for i in xrange(size):
                b = rhoList[i] * numpy.dot(yList[i],q)
                q += sList[i] * (aList[i] - b)
        pk = -q
        # fix non-descent components
        non_descent = numpy.where(pk*gfk>=0)[0]
        pk[non_descent] = 0
        # find step size
        alpha_k, new_fval, xkp1 = simple_line_search_owlqn(f,old_fval,xk,pk,gfk,k,Cvec)
        if alpha_k is None:
            if disp:
                sys.stderr.write("Warning: Line search failed. Using the gradient instead.\n")
            alpha_k, new_fval, xkp1 = simple_line_search_owlqn(f,old_fval,xk,-gfk,gfk,k,Cvec)
            if alpha_k is None:
                warnflag = 2
                break
        avg_rel_impr = (fvalList[0] - new_fval) / (len(fvalList)*new_fval)
        if avg_rel_impr <= ftol and len(fvalList) > 5:
            break
        # update
        old_fval = new_fval
        if retall:
            allvecs.append(xkp1)
        sk = xkp1 - xk
        xk = xkp1
        gfkp1 = myfprime(xkp1)
        # find penalized subgradients
        gfkp1 = subgrad(xkp1,gfkp1,Cvec)
        yk = gfkp1 - gfk
        gfk = gfkp1
        if callback is not None:
            callback(xk)
        k += 1
        gnorm = vecnorm(gfk,ord=norm)
        if (gnorm <= gtol):
            break
        sList.append(sk)
        yList.append(yk)
        try:
            rhok = 1 / (numpy.dot(yk,sk))
        except ZeroDivisionError:
            rhok = 1000.
            if disp:
                sys.stderr.write("Divide-by-zero encountered: rhok assumed large\n")
        fvalList.append(old_fval)
        rhoList.append(rhok)
        if len(sList) > cache_size:
            sList.pop(0)
            yList.pop(0)
            rhoList.pop(0)
        if len(fvalList) > fval_cache_size:
            fvalList.pop(0)

    if disp or full_output:
        fval = old_fval
    if warnflag == 2:
        if disp:
            sys.stderr.write("Warning: All line searches failed.\n")
            sys.stderr.write("         Current function value: %f\n" % fval)
            sys.stderr.write("         Iterations: %d\n" % k)
            sys.stderr.write("         Function evaluations: %d\n" % func_calls[0])
            sys.stderr.write("         Gradient evaluations: %d\n" % grad_calls[0])

    elif k >= maxiter:
        warnflag = 1
        if disp:
            sys.stderr.write("Warning: Maximum number of iterations has been exceeded\n")
            sys.stderr.write("         Current function value: %f\n" % fval)
            sys.stderr.write("         Iterations: %d\n" % k)
            sys.stderr.write("         Function evaluations: %d\n" % func_calls[0])
            sys.stderr.write("         Gradient evaluations: %d\n" % grad_calls[0])
    else:
        if disp:
            sys.stderr.write("Optimization terminated successfully.\n")
            sys.stderr.write("         Current function value: %f\n" % fval)
            sys.stderr.write("         Iterations: %d\n" % k)
            sys.stderr.write("         Function evaluations: %d\n" % func_calls[0])
            sys.stderr.write("         Gradient evaluations: %d\n" % grad_calls[0])

    if full_output:
        retlist = xk, fval, gfk, func_calls[0], grad_calls[0], warnflag
        if retall:
            retlist += (allvecs,)
    else:
        retlist = xk
        if retall:
            retlist = (xk, allvecs)

    return retlist

def main():
    import time
    times = []
    algor = []
    x0 = [0.8,1.2,0.7]

    print "BFGS Quasi-Newton"
    print "================="
    start = time.time()
    x = optimize.fmin_bfgs(optimize.rosen, x0, fprime=optimize.rosen_der, maxiter=80)
    print x
    print optimize.rosen(x)
    times.append(time.time() - start)
    algor.append('BFGS Quasi-Newton\t')


    print "OWLQN"
    print "================="
    start = time.time()
    x = fmin_owlqn(optimize.rosen, x0, fprime=optimize.rosen_der, maxiter=80)
    print x
    print optimize.rosen(x)
    times.append(time.time() - start)
    algor.append('OWLQN\t\t\t')

    print
    print "\nMinimizing the Rosenbrock function of order 3\n"
    print " Algorithm \t\t\t       Seconds"
    print "===========\t\t\t      ========="
    for k in range(len(algor)):
        print algor[k], "\t -- ", times[k]

if __name__ == "__main__":
    main()
