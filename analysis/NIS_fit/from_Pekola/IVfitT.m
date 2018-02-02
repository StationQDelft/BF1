function [T_fit, vfit, ifit, T_slope, v_slope, i_slope] = IVfitT(vdata, idata, e, kb, RN_guess, zerogap_guess, gamma_guess, Ts_guess, tol)

vscale = 1e-6; % scaling
iscale = 1e-9; % scaling

%% Full fit
beta_fit = nlinfit(vdata(idata>0)/vscale, log(abs(idata(idata>0)/iscale)), @(b,x)log(abs(INIS(x*vscale, b(1), b(1), RN_guess, zerogap_guess, gamma_guess)/iscale)), [Ts_guess]);
T_fit = beta_fit(1);
vfit = vdata;
ifit = INIS(vfit, T_fit, T_fit, RN_guess, zerogap_guess, gamma_guess);

%% Linear slope fit 
range = linspace(5e-12, 400e-12, 100);                                      % fitting range
irange = idata > min(range) & idata < max(range);                           % fitting range
alpha_fit = polyfit(log(idata(irange)/iscale), vdata(irange)/vscale, 1);    % linear fit
T_slope = e*alpha_fit(1)*vscale/kb;
i_slope = idata;
v_slope = (alpha_fit(2) + alpha_fit(1)*log(i_slope/iscale))*vscale;

%% Plots
figure(1)
set(gca,'yscale','log')
hold on
xlabel('Vnis, mV');
ylabel('Inis, nA');
xlim([-100e-6, 210e-6].*1e3);
ylim([1e-8,1e+2]);
plot(vdata(idata>0)*10^3, idata(idata>0)*10^9, 'b.'); % data
plot(vdata(idata>0)*10^3, INIS(vdata(idata>0), T_fit, T_fit, RN_guess, zerogap_guess, gamma_guess)*10^9, 'r.-');     % full fit
plot(v_slope*10^3, i_slope*10^9, 'k-', 'LineWidth', 2);

% Fermi Distribution for N
    function FermiDist_N = f_N(x, TN, gap)
        
        beta_N = gap/(kb*TN);
        FermiDist_N = 1./(exp(beta_N.*x)+1);
        
    end
% Fermi Distribution for S
    function FermiDist_S = f_S(x, TS, gap)
        
        beta_S = gap/(kb*TS);
        FermiDist_S = 1./(exp(beta_S.*x)+1);
        
    end
% Density of States for S
    function DoS_S = n_S(x, gamma)
        
        top = x+1i*gamma;
        bottom = sqrt(top.^2-1);
        DoS_S = abs(real(top./bottom));
        
    end
    function Integral_I = I_integrand(x, Volt, TS, TN, RN, gap, gamma)
        
        Integral_I = n_S(x, gamma).*(f_N(x-e*Volt/gap, TN, gap)-f_S(x, TS, gap));
        
    end
% Current of the NIS
    function Inis_sum = INIS(Volt, TS, TN, RN, gap, gamma)
        B = (gap)/(e*RN);
        Inis_1 = quadv(@(x)I_integrand(x,Volt, TS, TN, RN, gap, gamma), -10, -1, tol);
        Inis_2 = quadv(@(x)I_integrand(x,Volt, TS, TN, RN, gap, gamma), -1, 1, tol);
        Inis_3 = quadv(@(x)I_integrand(x,Volt, TS, TN, RN, gap, gamma), 1, 10, tol);
        
        Inis_sum = B*(Inis_1 + Inis_2 + Inis_3);
    end
end