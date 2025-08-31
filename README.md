# Application-of-Machine-Learning-to-Investigate-Ion-Heating-Properties
This code framework addresses the entire workflow of the TS-6 270-channel Doppler spectroscopy system, including calibration, ICCD triggering, full-channel intensity versus wavelength analysis, Abel inversion, and ion temperature reconstruction.
The code conduct the whole steps from an ICCD shot to the ion temperature distribution figure with poloidal magnetic field. Both H and Ar ions are taken into considered. 
File explanation:
0. automaticlly reduce background, save as net asc file.
1. find out x and y position of every shot, generate excel
2. integral intensity L vs wavelength, also do abel inversion in this step. 
3. calculate epsilon, the local intensity
4. plot figure
5. culculate the temperature, save in the original file
6. plot local temperature profile.
