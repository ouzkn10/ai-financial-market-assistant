import numpy as np
from math import log, sqrt, exp, erf, pi

from config import (MIN_PROB_BULL_LONG, MAX_PROB_BEAR_LONG, NO_TRADE_LO, NO_TRADE_HI,
                    SP_DTE, SP_TARGET_DELTA, SP_ROLL_DTE)

def _phi(x): return 0.5*(1.0+erf(x/sqrt(2)))
def _n(x):   return 1.0/sqrt(2*pi)*exp(-0.5*x*x)

def bs_price_and_greeks(S, K, T, iv, r=0.0, typ="C"):
    if T<=0 or iv<=0 or S<=0 or K<=0:
        return {"price":0.0,"delta":0.0,"gamma":0.0,"theta":0.0,"vega":0.0}
    d1 = (log(S/K)+(r+0.5*iv*iv)*T)/(iv*sqrt(T))
    d2 = d1 - iv*sqrt(T)
    if typ.upper()=="C":
        price = S*_phi(d1) - K*exp(-r*T)*_phi(d2)
        delta = _phi(d1)
    else:
        price = K*exp(-r*T)*_phi(-d2) - S*_phi(-d1)
        delta = -_phi(-d1)
    gamma = _n(d1)/(S*iv*sqrt(T))
    vega  = S*_n(d1)*sqrt(T)
    theta = -(S*_n(d1)*iv)/(2*sqrt(T)) - r*K*exp(-r*T)*_phi(d2 if typ.upper()=="C" else -d2)
    return {"price":float(price),"delta":float(delta),"gamma":float(gamma),"theta":float(theta),"vega":float(vega)}

def pick_side(prob_up, ma200_up, momentum_ok):
    if NO_TRADE_LO < prob_up < NO_TRADE_HI:
        return "FLAT"
    if ma200_up and momentum_ok:
        return "LONG" if prob_up >= MIN_PROB_BULL_LONG else "FLAT"
    if (not ma200_up) and (not momentum_ok):
        return "SHORT" if prob_up <= MAX_PROB_BEAR_LONG else "FLAT"
    return "FLAT"

def choose_short_strangle_params(spot, iv, dte=SP_DTE, target_delta=SP_TARGET_DELTA):
    T = dte/365.0
    if iv<=0: iv = 0.2
    def inv_phi(p):
        import math
        a1=-3.969683028665376e+01; a2=2.209460984245205e+02; a3=-2.759285104469687e+02
        a4=1.383577518672690e+02; a5=-3.066479806614716e+01; a6=2.506628277459239e+00
        b1=-5.447609879822406e+01; b2=1.615858368580409e+02; b3=-1.556989798598866e+02
        b4=6.680131188771972e+01; b5=-1.328068155288572e+01
        c1=-7.784894002430293e-03; c2=-3.223964580411365e-01; c3=-2.400758277161838e+00
        c4=-2.549732539343734e+00; c5=4.374664141464968e+00; c6=2.938163982698783e+00
        d1=7.784695709041462e-03; d2=3.224671290700398e-01; d3=2.445134137142996e+00; d4=3.754408661907416e+00
        plow=0.02425; phigh=1-plow
        if p<plow:
            q=(math.sqrt(-2*math.log(p)))
            return (((((c1*q+c2)*q+c3)*q+c4)*q+c5)*q+c6)/((((d1*q+d2)*q+d3)*q+d4)*q+1)
        if phigh<p:
            q=(math.sqrt(-2*math.log(1-p)))
            return -(((((c1*q+c2)*q+c3)*q+c4)*q+c5)*q+c6)/((((d1*q+d2)*q+d3)*q+d4)*q+1)
        q=p-0.5; r=q*q
        return (((((a1*r+a2)*r+a3)*r+a4)*r+a5)*r+a6)*q/(((((b1*r+a2)*r+a3)*r+a4)*r+a5)*r+1)
    z = inv_phi(1.0-target_delta)
    wing = float(iv*sqrt(T)*z)
    call_k = spot*(1+wing)
    put_k  = spot*(1-wing)
    return {"call_k":call_k, "put_k":put_k, "dte":dte}

def strangle_long_pnl_components(S0, S1, iv0, iv1, dte_days, call_k, put_k, r=0.0):
    """Return per-leg Greeks and long-option PnL components over window.
       Long leg approx: pnl = delta*dS + theta*dt + vega*dIV
    """
    T0 = dte_days/365.0
    T1 = max(0.0, (dte_days-1)/365.0)
    T = max(1e-9, (T0+T1)/2.0)
    dS = S1 - S0
    dIV = (iv1 - iv0) if (iv1 is not None and iv0 is not None) else 0.0
    gC = bs_price_and_greeks(S0, call_k, T, max(1e-6, iv0), r, typ="C")
    gP = bs_price_and_greeks(S0, put_k,  T, max(1e-6, iv0), r, typ="P")
    dt_year = 1/365.0
    pnlC = gC["delta"]*dS + gC["theta"]*dt_year + gC["vega"]*dIV
    pnlP = gP["delta"]*dS + gP["theta"]*dt_year + gP["vega"]*dIV
    return {"call":gC, "put":gP, "pnlC":pnlC, "pnlP":pnlP, "dS":dS, "dIV":dIV}
