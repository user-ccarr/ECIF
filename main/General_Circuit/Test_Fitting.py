# -*- coding: utf-8 -*-

#Import the necessary libraries
import numpy
import Fitting as fit
import Bootstrap as boot
import matplotlib.pyplot as plt
#For setting ticks on plot
from matplotlib.ticker import AutoMinorLocator
#Get user parameters
import config
#Get circuit of interest
import Circuits as cir
#For generating TIF files
from PIL import Image

#Acquire user input from config file
params = config.Initial_Parameters
modelname = config.Circuit_Type
filename = config.Filename
FreqLB = config.Frequency_Domain[0]
FreqUB = config.Frequency_Domain[1]

#Open test file
file=open(filename, 'r', encoding='cp1252')

#Initialize lists
F=[]
R=[]
Im=[]

#Read in the file
for line in file.readlines()[1:]:
    fields=line.split(',')
    Fre = float(fields[0])
    if Fre >= FreqLB and Fre <= FreqUB:
        F=F+[float(fields[0])]
        R=R+[float(fields[1])]
        Im=Im+[float(fields[2])]

#Form data into complex array
FArr=numpy.array(F)
RArr=numpy.array(R)
ImArr=numpy.array(Im)*1j
TotArr=RArr+ImArr

#Fit the data
fit_result = fit.custom_fitting(F, TotArr, params)
Fitted_variables = fit_result.x

#Obtain the residuals
residuals = fit.res_vec( Fitted_variables, FArr, TotArr)

#Bootstrap to get error and generate final model
boot_params = boot.strap(residuals, FArr, TotArr, Fitted_variables)
boot_generation, dummy1, dummy2 = cir.Z(boot_params, FArr, modelname)
Real_Boot_Fit = boot_generation.real
Imag_Boot_Fit = boot_generation.imag

#Plot this data
ImArrp = numpy.array(Im)
fig, ax = plt.subplots(figsize=(5,5),dpi=300)
ax.plot(RArr, -ImArrp, 'o', color = 'black', linewidth=2, label="Measured")
ax.plot(Real_Boot_Fit, -Imag_Boot_Fit, '-', color = 'blue', linewidth=2, label="Fit")
legend = ax.legend(loc='upper left', fontsize='medium')

#Get max impedance to square the plot
Rs = numpy.concatenate((RArr, -ImArrp, Real_Boot_Fit, -Imag_Boot_Fit))
maxest=Rs.max()
ax.set_xlim([0,maxest+0.1])
ax.set_ylim([0,maxest+0.1])
ax.set_xlabel(r'R $\mathregular{(\Omega\bullet cm^{2})}$', size='x-large')
ax.set_ylabel(r'-Im $\mathregular{(\Omega\bullet cm^{2})}$', size='x-large')

ax.tick_params(axis='both', direction='in', width = 1.0, length = 3)
ax.xaxis.set_minor_locator(AutoMinorLocator(4))
ax.xaxis.set_tick_params(which='minor', top = 'off', direction='in')
ax.yaxis.set_minor_locator(AutoMinorLocator(4))
ax.yaxis.set_tick_params(which='minor', right = 'off', direction='in')

legend.get_frame().set_edgecolor('#ffffff')
plt.savefig("EIS.png")
png0 = Image.open("EIS.png")
png0.save("EIS.tiff", dpi=(300,300))
plt.clf()
