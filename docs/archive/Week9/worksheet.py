def kingman_chain(stations, lam, Ca2_in=1.0):
    # stations: list of dicts
    # keys: mu, mtbf_hr, mttr_hr, Cs2_nom
    
    # Returns:
    # list of dicts
    # A, rho_eff, Cs2_eff, Wq_pred_min, Cd2
    
    results = []
    
    for stn in stations:
        mu = stn['mu']
        tp = 1.0 / mu  # mean processing time (hr) [GIVEN]
        A = stn['mtbf_hr'] / (stn['mtbf_hr'] + stn['mttr_hr'])  # [GIVEN]
        mu_eff = mu * A  # effective service rate [GIVEN]
        
        # COMPLETE (Blank 1)
        Cs2_eff = stn['Cs2_nom'] + A * (1 - A) * (stn['mttr_hr'] / tp)**2
        
        # Hopp & Spearman (Blank 2)
        rho_eff = min(lam / mu_eff, 0.9999) # lam / mu_eff, capped at 0.9999
        
        if rho_eff >= 1.0:
            Wq_pred_min = float('inf')
        else:
            Wq_pred_min = (rho_eff / (1 - rho_eff)) \
                          * ((Ca2_in + Cs2_eff) / 2.0) \
                          / mu_eff * 60  # convert hr -> min [GIVEN]
                          
        # Departure Theorem (Blank 3)
        Cd2 = (1 - rho_eff**2) * Ca2_in + (rho_eff**2) * Cs2_eff
        
        results.append(dict(
            A=round(A, 4), rho_eff=round(rho_eff, 4),
            Cs2_eff=round(Cs2_eff, 4),
            Wq_pred_min=round(Wq_pred_min, 2),
            Cd2=round(Cd2, 4)))
            
        Ca2_in = Cd2  # carry departure variability to next station [GIVEN]
        
    return results

# Reference line parameters
line = [
    dict(mu=10, mtbf_hr=200, mttr_hr=45/60, Cs2_nom=1.0),  # M01
    dict(mu=10, mtbf_hr=180, mttr_hr=45/60, Cs2_nom=1.0),  # M02
    dict(mu=10, mtbf_hr=300, mttr_hr=30/60, Cs2_nom=1.0)   # M03
]

for i, r in enumerate(kingman_chain(line, lam=8.0)):
    print(f"M0{i+1}: {r}")