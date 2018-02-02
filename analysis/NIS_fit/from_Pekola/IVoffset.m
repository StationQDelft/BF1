function [V_offset, I_offset] = IVoffset (xdata, ydata)

[xdata, ui] = unique(xdata(:));
ydata = ydata(ui);

nsmooth = 10; % averages over 10 points
I_probe = 0.05e-9; % + and - current at which we start
v_guess = 180e-6;
V_offset = 0; % initial offset
I_offset = 3e-12; % initial offset
v_pos    = v_guess;
v_neg    = -v_guess;

ydata_smooth = smooth(ydata,nsmooth)/I_probe; 

xdata1        = [-1 xdata.' 1];
ydata_smooth1 = [-1 ydata_smooth.' 1];

yfun = @(x)(interp1(xdata1, ydata_smooth1, x, 'linear', 'extrap')); 

opts = optimset('TolX', 1e-8);
for n = 1:100  % number of iterations
    v_pos = fzero(@(x)(yfun(x+V_offset)-1-I_offset), v_pos, opts); 
    v_neg = fzero(@(x)(yfun(x+V_offset)+1-I_offset), v_neg, opts);
    V_offset = V_offset + (v_pos+v_neg)/2;
    I_offset = yfun(V_offset);
end

I_offset = I_probe * I_offset;
end