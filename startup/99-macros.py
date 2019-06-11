import epics
import numpy as np
import bluesky.plans as bp
import pandas as pd

def help_fmx():
    """List FMX beamline functions with a short explanation"""
    
    print("""
    FMX beamline functions:
    
    focus_scan()    - Take microscope images with changing focus
    get_energy()    - Return HDCM energy in eV
    hdcm_rock()     - Scan HDCM crystal 2 pitch to maximize flux on BPM1
    ivu_gap_scan()  - Scan IVU21 gap against a BPM intensity signal and go to peak
    mirror_scan()   - Pencil beam scan of HFM and KB
    rd3d_calc()     - Dose estimate with RADDOSE3D
    set_beamsize()  - CRL settging to expand beam
    set_energy()    - Set undulator, HDCM, HFM and KB settings for a certain energy
    set_influence)  - Set HV power supply influence function voltage step
    simple_ascan()  - Scan a motor against a detector
    wire_scan()     - Scan a Cr nanowire and plot Cr XRF signal to determine beam size
    xf_bragg2e()    - Returns Energy in eV for given Bragg angle t in deg or rad
    xf_e2bragg()    - Returns Bragg angle t in deg for given Energy in eV
    
    Use help() to get more info, e.g. help(set_energy)
    """)


def get_energy():
    """
    Returns the current photon energy in eV derived from the DCM Bragg angle
    """
    
    energy = epics.caget('XF:17IDA-OP:FMX{Mono:DCM-Ax:E}Mtr.VAL')
    
    return energy


def get_fluxKeithley():
    """
    Returns Keithley diode current derived flux.
    """
    
    keithFlux = epics.caget('XF:17IDA-OP:FMX{Mono:DCM-dflux}')
    
    return keithFlux


def set_fluxBeam(flux):
    """
    Sets the flux reference field.
    
    flux: Beamline flux at sample position for transmisison T = 1.  [ph/s]
    """
    
    error = epics.caput('XF:17IDA-OP:FMX{Mono:DCM-dflux-M}', flux)
    
    return error


def slit1_flux_reference(flux_df,slit1Gap):
    """
    Sets Slit 1 X gap and Slit 1 Y gap to a specified position,
    and returns flux reference values to a provided pandas DataFrame.
    
    
    Parameters
    ----------
    
    slit1Gap: float
        Gap value for Slit 1 X and Y [um]
    
    flux_df: pandas DataFrame with fields:
        Slit 1 X gap [um]
        Slit 1 Y gap [um]
        Keithley current [A]
        Keithley flux [ph/s]
        BPM1 sum [A]
        BPM4 sum [A]
        
    """
    
    slits1.x_gap.move(slit1Gap)
    slits1.y_gap.move(slit1Gap)
    
    flux_df.at[slit1Gap, 'Slit 1 X gap [um]'] = slit1Gap
    flux_df.at[slit1Gap, 'Slit 1 Y gap [um]'] = slit1Gap
    flux_df.at[slit1Gap, 'Keithley current [A]'] = keithley.value
    flux_df.at[slit1Gap, 'Keithley flux [ph/s]'] = get_fluxKeithley()
    flux_df.at[slit1Gap, 'BPM1 sum [A]'] = bpm1.sum_all.value
    flux_df.at[slit1Gap, 'BPM4 sum [A]'] = bpm4.sum_all.value


def fmx_flux_reference(slit1GapList = [2000, 1000, 600, 400]):
    """
    Sets Slit 1 X gap and Slit 1 Y gap to a list of settings,
    and returns flux reference values in a pandas DataFrame.
    
    Parameters
    ----------
    
    slit1GapList: float (default=[2000, 1000, 600, 400])
        A list of gap values [um] for Slit 1 X and Y
    
    
    Returns
    -------
    
    flux_df: pandas DataFrame with fields
        Slit 1 X gap [um]
        Slit 1 Y gap [um]
        Keithley current [A]
        Keithley flux [ph/s]
        BPM1 sum [A]
        BPM4 sum [A]
        
    Examples
    --------
    fmx_flux_reference()
    flux_df=fmx_flux_reference()
    flux_df
    fmx_flux_reference(slit1GapList = [2000, 1500, 1000])
        
    """
    
    flux_df = pd.DataFrame(columns=['Slit 1 X gap [um]',
                                    'Slit 1 Y gap [um]',
                                    'Keithley current [A]',
                                    'Keithley flux [ph/s]',
                                    'BPM1 sum [A]',
                                    'BPM4 sum [A]',
                                   ])
    
    for slit1Gap in slit1GapList:
        slit1_flux_reference(flux_df,slit1Gap)
        
    return flux_df


def set_crl(crlSlider,inOut):
    '''
    Set EPICS PVs to move CRLs in or out
    
    crlSlider: Example for FMX slider No4: CRL_V2A='XF:17IDC-OP:FMX{CRL:04}Cmd:'
    inOut: 0 for slider OUT, 1 for IN
    '''
    
    # TODO: Consider using try/exceptions?
    
    if inOut:
        error = epics.caput(crlSlider+'In-Cmd',1)
    else:
        error = epics.caput(crlSlider+'Out-Cmd',1)
    
    return error


def set_beamsize(sizeV, sizeH):
    """
    Sets Compound Refractive Lenses (CRL) to defocus the beam
    
    sizeV: Vertical expansion
      'V0' no expansion
      'V1': 1 V CRL, for a V beam size of ~10um
      
    sizeH: Horizontal expansion
      'H0': no expansion
      'H1': 2 H CRLs, for a H beam size of ~10um
    
    Examples
    set_beamsize('V1','H1')
    set_beamsize('V1','H0')
    """
    
    CRL_VS ='XF:17IDC-OP:FMX{CRL:02}Cmd:'  # 1st bank with V slit
    CRL_V2A='XF:17IDC-OP:FMX{CRL:04}Cmd:'  # 1st bank with 2 V lenses
    CRL_V1A='XF:17IDC-OP:FMX{CRL:08}Cmd:'  # 1st bank with 1 V lens. Flipped for debugging
    CRL_V1B='XF:17IDC-OP:FMX{CRL:06}Cmd:'  # 2nd bank with 1 V lens. Flipped for debugging
    CRL_HS ='XF:17IDC-OP:FMX{CRL:01}Cmd:'  # 1st bank with H slit
    CRL_H4A='XF:17IDC-OP:FMX{CRL:03}Cmd:'  # 1st bank with 4 H lenses
    CRL_H2A='XF:17IDC-OP:FMX{CRL:05}Cmd:'  # 1st bank with 2 H lenses
    CRL_H1A='XF:17IDC-OP:FMX{CRL:07}Cmd:'  # 1st bank with 1 H lens
    CRL_H1B='XF:17IDC-OP:FMX{CRL:09}Cmd:'  # 2nd bank with 1 H lens
    
    if get_energy()<9000.0:
        print('Warning: For energies < 9 keV, use KB mirrors to defocus, not CRLs')
    
    if sizeV == 'V0':
        set_crl(CRL_VS,0)
        set_crl(CRL_V2A,0)
        set_crl(CRL_V1A,0)
        set_crl(CRL_V1B,0)
    elif sizeV == 'V1':
        set_crl(CRL_VS,1)
        set_crl(CRL_V2A,0)
        set_crl(CRL_V1A,0)
        set_crl(CRL_V1B,1)
    else:
        print("Error: Vertical size argument has to be \'V0\' or  \'V1\'")
    
    if sizeH == 'H0':
        set_crl(CRL_H4A,0)
        set_crl(CRL_H2A,0)
        set_crl(CRL_H1A,0)
        set_crl(CRL_H1B,0)
    elif sizeH == 'H1':
        set_crl(CRL_H4A,0)
        set_crl(CRL_H2A,1)
        set_crl(CRL_H1A,1)
        set_crl(CRL_H1B,1)
    else:
        print("Error: Horizontal size argument has to be \'H0\' or  \'H1\'")
    
    return


def set_influence(electrode, bimorph, bank):
    """
    Step up/down bimorph mirror electrodes for influence function measurements.
    
    The routine decreases the (electrode-1) electrode by the step size set for the bank,
    then increases the chosen electrode by the step size. Step size has to be set through the 
    PS web server interface or the IOC.
    
    Interface to Spellman HV power supply.
    
    electrode: Electrode number
    
    bimorph: Power supply, allowed values are ('hfm', 'kb')
    
    bank: Voltage bank, 1 for HFM and VKB, 2 for HKB
    
    Examples:
    for i in range(16):
        set_influence(i, 'kb', 1)
        set_influence(i, 'kb', 1)
        RE(mirror_scan('kbv', -1000, 1000, 400, camera=cam_8))
        db[-1].table().to_csv('/tmp/20190319_1544_vkb_pitch_2538urad_infl20190319_{0:0{width}}.csv'.format(i, width=2))
    
    for i in range(16,32):
        set_influence(i, 'kb', 2)
        set_influence(i, 'kb', 2)
        RE(mirror_scan('kbh', -700, 700, 400, camera=cam_8))
        db[-1].table().to_csv('/tmp/20190319_1753_hkb_2390urad_infl20190319_{}.csv'.format(i))
    
    """
    allowed_bimorphs = ('hfm', 'kb')
    
    if bimorph not in allowed_bimorphs:
        print("bimorph should be one of", allowed_bimorphs)
        return    
    
    if electrode < 0 or electrode > 31:
        print("electrode must be between 0 and 31")
        return
    
    if bimorph == 'hfm':
        prefix = 'XF:17IDA-OP:FMX{Mir:HFM-PS}:'
    elif bimorph == 'kb':
        prefix = 'XF:17IDC-OP:FMX{Mir:KB-PS}:'
        
    bank_pv = epics.PV(prefix+'BANK_NO_32')
    incr_pv = epics.PV(prefix+'INCR_U_CMD.A')
    decr_pv = epics.PV(prefix+'DECR_U_CMD.A')        
    step_pv = epics.PV(prefix + 'U_STEP_MON.A')
    demand_pvs = [epics.PV(prefix + 'U{}_CURRENT_MON'.format(i)) for i in range((bank-1)*16, bank*16)]
    
    bank_pv.put(bank-1, wait=True)
    time.sleep(0.5)
    step = step_pv.get()
    demands = [pv.get() for pv in demand_pvs]
    new_demands = demands[:]
    
    i = electrode if electrode < 16 else electrode-16
    if i > 0:
        new_demands[i - 1] -= step
    new_demands[i] += step
    
    for diff in np.diff(np.array(new_demands)):
        if abs(diff) > 500:
            print("got difference between values larger than 500")
            return
    
    if i > 0:
        print("decrementing electrode", electrode - 1, "by", step)
        decr_pv.put(electrode - 1)
    print("incrementing electrode", electrode, "by", step)
    incr_pv.put(electrode)

# RD3D_calc Raddose3D interface

import subprocess
from numpy.lib import recfunctions as rfn  # needs to be imported separately
from shutil import copyfile
import fileinput
import sys

def replaceLine(file,searchExp,replaceExp):
    for line in fileinput.input(file, inplace=1):
        if searchExp in line:
            line = replaceExp
        sys.stdout.write(line)

def run_rd3d(inputFileName):
    prc = subprocess.Popen(["java", "-jar", "raddose3d.jar", "-i", inputFileName],
        stdout=subprocess.PIPE,
        universal_newlines=True)
    out = prc.communicate()[0]
    return out

def rd3d_calc(flux=3.5e12, energy=12.66,
              beamType='GAUSSIAN', fwhmX=2, fwhmY=1, collimationX=10, collimationY=10,
              wedge=0, exposureTime=1,
              translatePerDegX=0, translatePerDegY=0, translatePerDegZ=0,
              dimX=20, dimY=20, dimZ=20,
              pixelsPerMicron=2, angularResolution=2,
              templateFileName = 'rd3d_input_template.txt'):
    """
    ---
    RADDOSE3D dose estimate
    
    This version calculates dose values for an average protein crystal.
    The estimates need to be adjusted proportionally for a crystal if it is more/less sensitive.
    
    All paramaters listed below can be set. If they are not set explicitly, RADDOSE3D will use
    the listed default value.
    
    A complete manual with explanations is available at
    https://github.com/GarmanGroup/RADDOSE-3D/blob/master/doc/user-guide.pdf
    
    Photon flux [ph/s]: flux=3.5e12
    Photon energy [keV]: energy=12.66,
    Beamtype (GAUSSIAN | TOPHAT): beamType='GAUSSIAN'
    Vertical beamsize FHWM [um]: fwhmX=1
    Horizontal beamsize FHWM [um]: fwhmY=2
    Vertical collimation (for TOPHAT beams this is the size) [um]: collimationX=10
    Horizontal collimation (for TOPHAT beams this is the size) [um]: collimationY=10
    Omega range [deg]: wedge=0
    Exposure time for the complete wedge [s]: exposureTime=1
    Translation per degree V [um]: translatePerDegX=0
    Translation per degree H [um]: translatePerDegY=0
    Translation along beam per degree [um]: translatePerDegZ=0
    Crystal dimension V [um]: dimX=20
    Crystal dimension H [um]: dimY=20
    Crystal dimension along beam [um]: dimZ=20
    Pixels per micron: pixelsPerMicron=2
    Angular resolution: angularResolution=2
    Template file (must be in same dir as this notebook): templateFileName = 'rd3d_input_template.txt'
    
    The return value is a structured numpy array. You can use it for follow-up calculations
    of the results returned by RADDOSE3D in "output-Summary.csv". Call the return variable
    to find the field names.
    
    Example:
    > rd3d_out = rd3d_calc(flux=1.35e12, exposuretime=0.01, dimx=1, dimy=1, dimz=1)
    """
        
    inputFileName = "rd3d_input.txt"
    outputFileName = "output-Summary.csv"

    copyfile(templateFileName, inputFileName)

    replaceLine(inputFileName,"FLUX",'FLUX {:.2e}\n'.format(flux))
    replaceLine(inputFileName,"ENERGY",'ENERGY {:.2f}\n'.format(energy))
    replaceLine(inputFileName,"TYPE GAUSSIAN",'TYPE {:s}\n'.format(beamType))
    replaceLine(inputFileName,"FWHM",'FWHM {:.1f} {:.1f}\n'.format(fwhmX,fwhmY))
    replaceLine(inputFileName,"COLLIMATION",'COLLIMATION RECTANGULAR {:.1f} {:.1f}\n'.format(collimationX,collimationY))
    replaceLine(inputFileName,"WEDGE",'WEDGE 0 {:0.1f}\n'.format(wedge))
    replaceLine(inputFileName,"EXPOSURETIME",'EXPOSURETIME {:0.3f}\n'.format(exposureTime))
    replaceLine(inputFileName,"TRANSLATEPERDEGREE",
                'TRANSLATEPERDEGREE {:0.1f} {:0.1f} {:0.1f}\n'.format(translatePerDegX,translatePerDegY,translatePerDegZ))
    replaceLine(inputFileName,"DIMENSION",'DIMENSION {:0.1f} {:0.1f} {:0.1f}\n'.format(dimX,dimY,dimZ))
    replaceLine(inputFileName,"PIXELSPERMICRON",'PIXELSPERMICRON {:0.1f}\n'.format(pixelsPerMicron))
    replaceLine(inputFileName,"ANGULARRESOLUTION",'ANGULARRESOLUTION {:0.1f}\n'.format(angularResolution))
    
    out = run_rd3d(inputFileName)
    print(out)
    
    rd3d_out = np.genfromtxt(outputFileName, delimiter=',', names=True)
    print("\n=== Results ===")
    # append_fields has issues with 1d arrays, use reshape() and [] to make len() work on size 1 array:
    # https://stackoverflow.com/questions/53137822/adding-a-field-to-a-structured-numpy-array-4
    rd3d_out = rd3d_out.reshape(1)
    print("Diffraction weighted dose = " + "%.3f" % rd3d_out['DWD'] + " MGy")
    print("Max dose = " + "%.3f" % rd3d_out['Max_Dose'] + " MGy")  
    t2gl = exposureTime * 30 / rd3d_out['DWD']  # Time to Garman limit based on diffraction weighted dose
    rd3d_out = rfn.append_fields(rd3d_out,'t2gl',[t2gl],usemask=False)
    print("Time to Garman limit = " + "%.3f" % rd3d_out['t2gl'] + " s")
    
    return rd3d_out

# X-ray utility functions

def xf_bragg2e(t, h=1, k=1, l=1, LN=0):
    """
    Returns Energy in eV for given Bragg angle t in deg or rad
     
    t: Bragg angle [deg or rad]
    h,k,l: Miller indices of Si crystal (optional). Default h=k=l=1
    LN: Set to 1 for 1st xtal cooled and 2nd xtal RT. Default 0
    
    Python version of IDL a2e.pro c/o Clemens Schulze Briese
    """
    
    if LN: LN=1
    tt = t*np.pi/180 if t > 1 else t
    
    d0 = 2*5.43102*(1-2.4e-4*LN)/np.sqrt(h^2+k^2+l^2)
    E = 12398.42/(d0*np.sin(tt))
    
    return E

def xf_e2bragg(E, h=1, k=1, l=1):
    """
    Returns Bragg angle t in deg for given Energy in eV
    
    E: Energy in eV. If E<100, assume it's keV and convert.
    h,k,l: Miller indices of Si crystal optional
    
    Python version of IDL angle.pro c/o Clemens Schulze Briese
    """
    
    if E<100: E=E*1e3
    
    d0 = 2*5.43102/np.sqrt(h^2+k^2+l^2)
    t = np.arcsin(12398.42/d0/E) * 180/np.pi;
    
    return t
