clear all
close all

matfiles = dir('C:\AALTO\Espoo\PhD\Delft\MatlabPrograms\*.txt');

%% Parameters
e = 1.602e-19;
kb = 1.3806488e-23;

RN_guess = 7.737e+03;
gamma_guess = 2.2e-5;
zerogap = 200e-6;
zerogap_guess = zerogap*e;
Ts_guess = 0.08836;
tol = 1e-9;

for k = 1:1;
%% Data    
    data = load(['C:\AALTO\Espoo\PhD\Delft\MatlabPrograms\' matfiles(k).name]);
    
    v_data = data(:,2);
    i_data = data(:,1);
    points = length(v_data);
    
    for i = 1
        
        range = 1:length(v_data);
%% Offset correction        
        [voffset, ioffset] = IVoffset(v_data(range), i_data(range)); 
        x(i).V = v_data(range)-voffset;
        x(i).I = i_data(range)-ioffset;
        
        
%% Fitting procedure
        [x(i).T_result, vfit, ifit, x(i).Tslope_result, vslope, islope] =  IVfitT(x(i).V, x(i).I, e, kb, RN_guess, zerogap_guess, gamma_guess, Ts_guess, tol);   
 
%% Display Te extracted from the fits        
        display(x(i).T_result)
        display(x(i).Tslope_result)
        
    end
    
end