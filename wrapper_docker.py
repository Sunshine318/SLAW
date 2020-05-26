
import os
import multiprocessing
import yaml
import sys
import psutil
import math
import shutil

##We import the module of python processing.
sys.path.append('/pylcmsprocessing')
from pylcmsprocessing.model.helper.UI import UI
from pylcmsprocessing.model.experiment import Experiment,check_peakpicking
from pylcmsprocessing.model.steps.optimize_parameters import ParametersOptimizer
from pylcmsprocessing.model.helper.parameters_handler import ParametersFileHandler
from pylcmsprocessing.common.time_evaluation import Timer
import pylcmsprocessing.common.references as pcr

if __name__=="__main__":
##Two thing to check the number of CPUs and the ocnsumed meory eventually.
    ###We determine the amount of memory allocated to each process
    timer = Timer()
    timer.store_point("wstart")
    avail_memory = (psutil.virtual_memory()[1] >> 20)
    ###We allocate the memory to each process
    num_cpus = multiprocessing.cpu_count()-1
    ###Two limits to check, the number of CPUs and the memory consumption eventually.
    #1.5 Go
    memory_by_core = 1048*1.2

    if "MEMORY" in os.environ:
        memory_by_core = int(math.floor(float(os.environ["MEMORY"])))
    else:
        ##We save it ofr optimization
        os.environ["MEMORY"] = str(math.floor(memory_by_core))


    ##This is the number of thread
    ncores = avail_memory//memory_by_core

    ###Now we check if this number is bigger than the number of thread
    if ncores <= num_cpus:
        num_cpus = ncores
        if not "MEMORY" in os.environ:
            memory_by_core = avail_memory/num_cpus

    if "LSB_MAX_NUM_PROCESSORS" in os.environ and int(os.environ["LSB_MAX_NUM_PROCESSORS"])<num_cpus:
        num_cpus = int(os.environ["LSB_MAX_NUM_PROCESSORS"])

    if "NCORES" in os.environ and int(os.environ["NCORES"])<num_cpus:
        num_cpus = int(os.environ["NCORES"])

    if "MEMORY" in os.environ:
        memory_by_core = int(os.environ["MEMORY"])

    ###We set the JAVA option for the peak picking evnetually
    os.environ["JAVA_OPTS"] = "-Xms"+str(math.floor(memory_by_core/2))+"m -Xmx"+str(math.floor(memory_by_core)-200)+"m"
    ##We output System information
    print("Total memory available: "+str(avail_memory)+" and "+str( multiprocessing.cpu_count())+" cores. The workflow will use "+str(math.floor(memory_by_core))+ " Mb by cores on "+str(num_cpus)+" cores.")

    MANDATORY_ARGS = ["INPUT", "OUTPUT"]
    if os.environ['OUTPUT'].startswith('/sauer1') or os.environ['INPUT'].startswith('/sauer1'):
        MANDATORY_ARGS.append("USERNAME")

    if not all(env in os.environ for env in MANDATORY_ARGS):
        raise Exception(",".join(MANDATORY_ARGS)+' and  are mandatory arguments')
    #The path of the mounted directory is always output
    OUTPUT_DIR = os.environ['OUTPUT']
    if OUTPUT_DIR.startswith("/sauer1"):
        if not os.path.isdir(OUTPUT_DIR):
            print("Output directory "+OUTPUT_DIR+"does not exist")

    LOG = os.path.join(OUTPUT_DIR,"log.txt")

    # subprocess.call("java "+os.environ["JAVA_OPTS"]+" -XshowSettings:vm -version  >> "+LOG+" 2>&1",shell=True)
    #The raw files are always mounted into raw_files
    INPUT = os.environ['INPUT']
    if INPUT.startswith("/sauer1"):
        if not os.path.isdir(INPUT):
            raise Exception('Directory '+INPUT+' does not exist' )

    ##The yaml file is always putt in the paramters.text
    PATH_YAML = os.path.join(OUTPUT_DIR,"parameters.txt")
    PATH_XML = os.path.join(OUTPUT_DIR,"batch_xml_adap.xml")
    PATH_TEMP_XML = os.path.join(OUTPUT_DIR,"batch_xml_adap_temp.xml")

    PATH_TARGET = os.path.join(INPUT,"target.csv")
    if os.path.isfile(PATH_TARGET):
        print("Detected target list")

    setup_params = False
    #If the yaml parameter file already exist we just read it, else. we don t read it
    #We put a message if the output is not here.
# THE sample database is always calculated before doing any processing
    PATH_DB = os.path.join(OUTPUT_DIR, "temp_processing_db.sqlite")
    DB_STORAGE = os.path.join(OUTPUT_DIR, "temp_optim", "db_storage")

    if os.path.isdir("/sauer1"):
        PATH_DB = "/temp_processing_db.sqlite"
        DB_STORAGE = "/db_storage"

    if "FOPTIM" in os.environ:
        num_optim = int(os.environ["FOPTIM"])
    else:
        num_optim = 5

    # LOG = "/log.txt"
    #Procesinf of the pipeline eventually.
    path_save_db = os.path.join(OUTPUT_DIR,"processing_db.sqlite")
    if os.path.isfile(path_save_db):
        shutil.copyfile(path_save_db,PATH_DB)
    exp = Experiment(PATH_DB,save_db = path_save_db,reset=False,temp_outdir=OUTPUT_DIR)
    ###The polarity computed at this step does not need to mahke any sense.
    path_ms2 = None
    if "MS2" in os.environ:
        path_ms2 = os.environ["MS2"]
    ###We try to guess the polarity form the middle file.
    pol = exp.guess_polarity(INPUT)
    print("Polarity detected: " + exp.polarity)
    exp.initialise_database(num_cpus, OUTPUT_DIR, pol, INPUT, ["ADAP"], 1, path_ms2=path_ms2)
    timer.store_point("winitialisation")
    timer.print_point("winitialisation")
    vui = UI(OUTPUT_DIR, INPUT, polarity=os.environ["POLARITY"], mass_spec="Exactive", num_workers=num_cpus,
         path_yaml=PATH_YAML)

    ###In all case the first table is generated.
    if not os.path.exists(vui.path_yaml):
        ###We just create a an empty yaml file
        vui.generate_yaml_files()
        vui.initialize_yaml_polarity(PATH_YAML, pol)
        print("Parameters file generated please tune the parameers and or parameters range before optimization.")
        exit(0)
    else:
        ph = ParametersFileHandler(vui.path_yaml)
        ##We check what is the given peakpicker.
        peakpicking = ph.get_peakpicking()
        peakpicking = check_peakpicking(peakpicking)

        if not ph.is_optimized():
            vui.generate_yaml_files()
            vui.initialize_yaml_polarity(PATH_YAML, pol)
            with open(vui.path_yaml, 'r') as stream:
                raw_yaml = yaml.safe_load(stream)

            num_points = int(raw_yaml["optimization"]["number_of_points"]["value"])
            max_its = int(raw_yaml["optimization"]["num_iterations"]["value"])
            optim_files = int(raw_yaml["optimization"]["files_used"]["value"])

            PATH_OPTIM = os.path.join(OUTPUT_DIR, "temp_optim")
            if not os.path.isdir(DB_STORAGE):
                os.makedirs(DB_STORAGE)

            ###We optimize the parameters
            par_opt = ParametersOptimizer(exp, PATH_OPTIM,DB_STORAGE,num_workers=num_cpus, input_par=PATH_YAML)
            par_opt.optimize_parameters(vui.path_yaml, optimizer=os.environ["OPTIM"], max_its=max_its,
                                        num_points=num_points,num_files =optim_files,num_cores=num_cpus)
            timer.store_point("woptimization")
            timer.print_point("woptimization")
            ###If there was optimiz\ation we have ot reset the otpoimization proces
            exp.reset_processing()

    if not os.path.isfile(PATH_XML):
        if peakpicking=="ADAP":
            vui.generate_MZmine_XML(path_xml=PATH_XML)
        print("An ADAP batch file has been generated in the "+OUTPUT_DIR+" directory, you ca use it to refine peakpicking parameters using MZmine.")
    exp.initialise_database(num_cpus,OUTPUT_DIR,vui.polarity,INPUT,["ADAP"], 1)
    # exp.building_inputs_single_processing(PATH_XML)
    ###We always read the yaml paramters file.
    with open(vui.path_yaml, 'r') as stream:
        raw_yaml = yaml.safe_load(stream)

    if peakpicking=="ADAP":
        exp.run_mzmine("/MZmine-2.52-Linux",PATH_XML,int(num_cpus*3),log = LOG)
        exp.correct_conversion()
        exp.post_processing_peakpicking_mzmine()
        ###If there is an MS2 folder we process it
        if "MS2" in os.environ:
            exp.extract_ms2(noise_level=float(raw_yaml["peakpicking"]["noise_level_ms2"]["value"]), output=pcr.OUT["ADAP"]["MSMS"])

    if peakpicking=="OPENMS":
        ###In this case arugment are read directly
        #run_openms(self, min_fwhm, max_fwhm, snt, ppm, min_int, max_outlier, min_points, quant
        min_fwhm = float(raw_yaml["peakpicking"]["peaks_deconvolution"]["peak_width"]["value"][0])*60
        max_fwhm = float(raw_yaml["peakpicking"]["peaks_deconvolution"]["peak_width"]["value"][1])*60
        sn = float(raw_yaml["peakpicking"]["peaks_deconvolution"]["SN"]["value"])
        min_int = float(raw_yaml["peakpicking"]["noise_level_ms1"]["value"])
        min_scan = math.floor(float(raw_yaml["peakpicking"]["traces_construction"]["min_scan"]["value"]))
        max_outlier = math.floor(float(raw_yaml["peakpicking"]["traces_construction"]["num_outliers"]["value"]))
        quant = raw_yaml["grouping"]["extracted_quantity"]["value"]
        ppm = float(raw_yaml["peakpicking"]["traces_construction"]["ppm"]["value"])
        exp.run_openms(min_fwhm, max_fwhm, sn, ppm, min_int, max_outlier, min_scan, quant,log = LOG)
        exp.extract_ms2(noise_level=float(raw_yaml["peakpicking"]["noise_level_ms2"]["value"]),output=pcr.OUT["OPENMS"]["MSMS"])
        exp.post_processing_peakpicking_openms()
    ###As openMS does not give nativelyt MS-MS
    timer.store_point("wpeakpicking")
    timer.print_point("wpeakpicking")

    intensity = str(raw_yaml["grouping"]["extracted_quantity"]["value"])
    exp.group_online(intensity=intensity,
        ppm = float(raw_yaml["grouping"]["ppm"]["value"]),
        mztol=float(raw_yaml["grouping"]["dmz"]["value"]),
        rttol=float(raw_yaml["grouping"]["drt"]["value"]),
        n_ref = int(raw_yaml["grouping"]["num_references"]["value"]),
        alpha=float(raw_yaml["grouping"]["alpha"]["value"]),
        ms2_mz_tol = float(raw_yaml["peakpicking"]['peaks_deconvolution']["ms2_mz_tol"]["value"]),
        ms2_rt_tol = float(raw_yaml["peakpicking"]['peaks_deconvolution']["ms2_rt_tol"]["value"]),
        log=LOG)
    timer.store_point("walignment")
    timer.print_point("walignment")
    main_adducts_str=raw_yaml["ion_annotation"]["main_adducts_"+exp.polarity]["value"]
    adducts_str = raw_yaml["ion_annotation"]["adducts_"+exp.polarity]["value"]
    successfully_processed = exp.annotate_ions(int(raw_yaml["ion_annotation"]["num_files"]["value"]),float(raw_yaml["ion_annotation"]["ppm"]["value"]),
        float(raw_yaml["ion_annotation"]["dmz"]["value"]),min_filter=raw_yaml["ion_annotation"]["min_filter"]["value"],
                adducts=adducts_str,main_adducts=main_adducts_str, max_workers=num_cpus)
    timer.store_point("wannotation")
    timer.print_point("wannotation")
    if successfully_processed:
        exp.post_processing(PATH_TARGET)
        exp.clean()
