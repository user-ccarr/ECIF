# -*- coding: utf-8 -*-

#Import the necessary libraries
import re
import numpy
import Fitting as fit
import Bootstrap as boot
import matplotlib.pyplot as plt
import pandas as pd
#For setting ticks on plot
from matplotlib.ticker import AutoMinorLocator
#Get user parameters
import config
#Get circuit of interest
import Circuits as cir
#For generating TIF files
from PIL import Image
#For command line commands
import os
#For moving and sorting files
import shutil

import seaborn as sns
        
#Acquire user input from config file
params = config.Initial_Parameters
modelname = config.Circuit_Type
FreqLB = config.Frequency_Domain[0]
FreqUB = config.Frequency_Domain[1]

ImpedanceFiles = []

#Get the files to be measured
HomeFiles=os.listdir()

pattern = re.compile(".csv$")  # Compile a regex
for line in HomeFiles:
    if pattern.search(line) != None:      # If a match is found 
        ImpedanceFiles.append(line)
    
for thing in ImpedanceFiles:

#Open test file
    file=open(thing, 'r', encoding='cp1252')

#Initialize lists
    F=[]
    R=[]
    Im=[]
    thetas=[]

#Read in the file
    for line in file.readlines()[1:]:
        fields=line.split(',')
        Fre = float(fields[0])
        if Fre >= FreqLB and Fre <= FreqUB:
            F=F+[float(fields[0])]
            R=R+[float(fields[1])]
            Im=Im+[float(fields[2])]
            thetas=thetas+[numpy.arctan(float(fields[2])/float(fields[1]))]

    file.close()
#Form data into complex array
    FArr=numpy.array(F)
    RArr=numpy.array(R)
    ImArr=numpy.array(Im)*1j
    TotArr=RArr+ImArr

#Fit the data
    fit_result, Param_Names = fit.custom_fitting(F, TotArr, params)
    Fitted_variables = fit_result.x

#Obtain the residuals
    residuals = fit.res_vec( Fitted_variables, FArr, TotArr)

#Bootstrap to get error and generate final model
    boot_params, corr = boot.strap(residuals, FArr, TotArr, Fitted_variables, Param_Names)
    result = cir.Z(boot_params, FArr, modelname)
    boot_generation = result.z
    Real_Boot_Fit = boot_generation.real
    Imag_Boot_Fit = boot_generation.imag
    Thetas_Fit = []
    i=0
    for x in Real_Boot_Fit:
        theta = numpy.arctan(Imag_Boot_Fit[i]/Real_Boot_Fit[i])
        Thetas_Fit = Thetas_Fit + [theta]
        i=i+1

    ###Lets output this data in a csv###
    ImArrp = numpy.array(Im)
    EISData=list(zip(FArr, RArr, -ImArrp, thetas, Real_Boot_Fit, -Imag_Boot_Fit, Thetas_Fit))
    EISdf = pd.DataFrame(data = EISData, columns=['F(Hz)', 'R(ohm)','-Im(ohm)', 'Theta(degrees)', 'Fit R(ohm)','Fit -Im(ohm)', 'Fit Theta(degrees)'])
    

#Covariance Plot
# Generate a mask for the upper triangle
    mask = numpy.zeros_like(corr, dtype=numpy.bool)
    mask[numpy.triu_indices_from(mask)] = True

# Set up the matplotlib figure
    f, ax = plt.subplots(figsize=(11, 9))

# Generate a custom diverging colormap
    cmap = sns.diverging_palette(255, 133, l=60, n=7, center="dark", as_cmap=True)

# Draw the heatmap with the mask and correct aspect ratio
    sns.heatmap(corr, mask=mask, cmap=cmap, vmax=1, center=0,
                square=True, linewidths=.5, cbar_kws={"shrink": .5})
    plt.savefig("Correlation Matrix.png")
    png0 = Image.open("Correlation Matrix.png")
    png0.save("Correlation Matrix.tiff", dpi=(300,300))
    plt.clf()

##Nyquist plot##
    fig, ax = plt.subplots(figsize=(5,5),dpi=300)
    ax.plot(RArr, -ImArrp, 'o', color = 'black', linewidth=2, label="Measured")
    ax.plot(Real_Boot_Fit, -Imag_Boot_Fit, '-', color = 'blue', linewidth=2, label="Fit")
    legend = ax.legend(loc='upper left', fontsize='medium')

#Get max impedance to square the plot
    Rs = numpy.concatenate((RArr, -ImArrp, Real_Boot_Fit, -Imag_Boot_Fit))
    maxest=Rs.max()
    ax.set_xlim([0,maxest+0.1])
    ax.set_ylim([0,maxest+0.1])
    ax.set_xlabel(r'R $\mathregular{(\Omega\bullet cm^{2})}$', size='large')
    ax.set_ylabel(r'-Im $\mathregular{(\Omega\bullet cm^{2})}$', size='large')

    ax.tick_params(axis='both', direction='in', width = 1.0, length = 3)
    ax.xaxis.set_minor_locator(AutoMinorLocator(4))
    ax.xaxis.set_tick_params(which='minor', top = 'off', direction='in')
    ax.yaxis.set_minor_locator(AutoMinorLocator(4))
    ax.yaxis.set_tick_params(which='minor', right = 'off', direction='in')

    legend.get_frame().set_edgecolor('#ffffff')
    plt.savefig("Nyquist.png")
    png0 = Image.open("Nyquist.png")
    png0.save("Nyquist.tiff", dpi=(300,300))
    plt.clf()

##Bode plot##
    plt.style.use('classic')
    Measured_Modulus = numpy.sqrt(RArr ** 2 + ImArrp ** 2)
    Fitted_Modulus = numpy.sqrt(Real_Boot_Fit ** 2 + Imag_Boot_Fit ** 2)

    fig, ax = plt.subplots(figsize=(10,5),dpi=300)
    ax.plot(FArr, Measured_Modulus, 'o', color = 'black', linewidth=2, label="Measured")
    ax.plot(FArr, Fitted_Modulus, '-', color = 'blue', linewidth=2, label="Fit")
    legend = ax.legend(loc='upper right', fontsize='medium')

    ax.set_xscale('log')
    ax.set_xlabel('Frequency (Hz)', size='large')
    ax.set_ylabel('|Z|', size='large')
    

    legend.get_frame().set_edgecolor('#ffffff')
    plt.savefig("Bode.png")
    png0 = Image.open("Bode.png")
    png0.save("Bode.tiff", dpi=(300,300))
    plt.clf()

#Thetas
    fig, ax = plt.subplots(figsize=(10,5),dpi=300)
    ax.plot(FArr, thetas, 'o', color = 'black', linewidth=2, label="Measured")
    ax.plot(FArr, Thetas_Fit, '-', color = 'blue', linewidth=2, label="Fit")
    legend = ax.legend(loc='lower right', fontsize='medium')

    ax.set_xscale('log')
    ax.set_xlabel('Frequency (Hz)', size='large')
    ax.set_ylabel(r'$\theta $', size='large')

    legend.get_frame().set_edgecolor('#ffffff')
    plt.savefig("Bode_Theta.png")
    png0 = Image.open("Bode_Theta.png")
    png0.save("Bode_Theta.tiff", dpi=(300,300))
    plt.clf()

#Clean up
    namesplit=thing.split(".")
    name=namesplit[0]
    os.makedirs(name+"Fitting Report")
    EISdf.to_csv(name + " Pattern Fit to Data.csv",index=False,header=True)
    os.makedirs("Plots")
    os.makedirs("Values")
    shutil.move(name + " Pattern Fit to Data.csv", "Values")
    shutil.move("Correlation Matrix.png","Plots")
    shutil.move("Correlation Matrix.tiff","Plots")
    shutil.move("Nyquist.png","Plots")
    shutil.move("Nyquist.tiff", "Plots")
    shutil.move("Bode.png", "Plots")
    shutil.move("Bode.tiff", "Plots")
    shutil.move("Bode_Theta.png", "Plots")
    shutil.move("Bode_Theta.tiff", "Plots")
    shutil.move('Fitted_Parameters.csv', "Values")
    shutil.move("Plots", name+"Fitting Report")
    shutil.move("Values", name+"Fitting Report")
