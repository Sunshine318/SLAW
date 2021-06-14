# SLAW

SLAW is a scalable containerized untargeted LC-MS processing workflow. The three core points of SLAW are:
 * Scalability: SLAW can process thousands of SAMPLES efficiently
 * Inclusion of 3 peak picking algorithms (Centwave, FeatureFinderMetabo, ADAP)
 * Parameters optimization: SLAW allows the parameters optimization for all the peak pickers considered, in an efficient manner.
 The source code here should not be used directly and is just shown as a reference if needed.
 
The recommended way to use SLAW is to download the associated *Docker* from the dockerHub like this:
```
docker pull adelabriere/slaw:latest
```
or from singularityHub.

## Current version : 1.0.0

## Running SLAW

Some example data are given in the test_data folder of this git folder. These data have been heavily filtered to allow quick testing. An example of input folder is given in the _test_data/mzML_ folder, and an example of parameters file (which will be generated by SLAW if you run it on an empty folder) is given in _test_data/parameters.txt_ an example of the complete output of SLAW without optimization is given in _test_data/output_. A zipped file containing the inputs, the only thing needed to run SLAW a  can be downloaded

Once this folder have been downloaded, and extracts at the location of your choice (PATH_INPUT), and create an empty anywhere to store the output (PATH_OUTPUT). The workflow can be run by opening a terminal, or on windows a Powershell (NOT Powershell ISE) and running:
```
docker run --rm -v PATH_FOLDER\mzML:/input -v PATH_OUTPUT:/output adelabriere/slaw:latest
```
If you specified the path correctly, you should see the following text:
```
2020-12-02|12:39:28|INFO: Total memory available: 7556 and 6 cores. The workflow will use 1257 Mb by core on 5 cores.
....
2020-12-02|12:39:31|INFO: Parameters file generated please check the parameters values/ranges and toggle optimization if needed.
```
Now a _parameters.txt_ which stores all the parameters of the processing. The processing can then be strated br rerunning the command line. SLAW takes the input parameters.txt and processes the data.
```
docker run --rm -v PATH_FOLDER\mzML:/input -v PATH_OUTPUT:/output adelabriere/slaw:latest
```
The optimization is switched off by default to avoid a long processing time. You can turn it on in the _parameters.txt_ file by setting the _optimization/need_optimization_ parameters to "True". If you choose to do so, the processing should take less than 1 hour to finish. If not, it should take less than 5 mins. If the workflow finished the

```
2020-12-02|12:39:37|INFO: Total memory available: 7553 and 6 cores. The workflow will use 1257 Mb by core on 5 cores.
2020-12-02|12:39:37|INFO: Guessing polarity from file:DDA1.mzML
2020-12-02|12:39:38|INFO: Polarity detected: positive
2020-12-02|12:39:39|INFO: STEP: initialisation TOTAL_TIME:2.05s LAST_STEP:2.05s
...
2020-12-02|12:41:04|INFO: STEP: gap-filling TOTAL_TIME:86.86s LAST_STEP:15.17s
2020-12-02|12:41:30|INFO: Annotation finished
2020-12-02|12:41:30|INFO: STEP: annotation TOTAL_TIME:112.74s LAST_STEP:25.87s
```
The outputs are generated in PATH_OUTPUT the complete outputs are:
 * datamatrices: The complete table with row corresponding to features or ions and the columns corresponding to a sample. Three flavors of datamatrices are generated.
 * fused_mgf: The consensus mfg spectra obtained, storing one ms-ms spectrum by features in the data matrices.
 * OPENMS/CENTWAVE/ADAP: Store the individual peak tables and ms-ms spectra for each sample.

 More information about the parameters and the workflow [can be found into the wiki.](https://github.com/adelabriere/SLAW/wiki).


<!-- ## Installing docker -->

<!-- Docker can be installed following this [tutorial](https://runnable.com/docker/install-docker-on-windows-10).
The whole installation process should take less than 15 minutes, mainly because you need to restart your computer.

After the installation is finished you have to add yourself to the docker-user group of ETH to run Docker. At the moment you have to do it yourself, to do so sign out of your session (Important : sign out) and log in the admin account of your computer (SYSBCPU) and find the local users group in the control panel :
![alt text](imgs/local_users.png)

Then on the windows click on the Groups folder in the middle panel, open the docker-users group. You  can then add yourself to the docker-users, using you ETH login (dalexis in my case). You can then log out of the SYSBCPU account
### Increasing processing power.
By default the docker virtual machine only take a small part of your computing power, however especially if you have a workstation. To do so right click on the docker icon at the right of your task bar :
 ![alt text](imgs/icon_docker.png)

And open the settings page :
 ![alt text](imgs/increasing_power.png) -->
<!--
The number of CPUs and the RAM will notably increase the speed of the peakpicking. One peakpicking experiment take 1.25Go of RAM approximately. After these modifications the docker engine will restart, which can take several minutes.

## Running the workflow

### Getting the last version of the workflow
Once docker is installed please run the Windows Powershell on windows or any Unix terminal. The workflow can then be installed directly form the "dockerhub" just by typing the following lines :
```
docker pull adelabriere/lcms_workflow_zamboni:latest
```
The required space is approximately 3 Go.

### Running the docker

_TLDR :_
```
docker run -it --cap-add=SYS_ADMIN --cap-add=DAC_READ_SEARCH --privileged -e INPUT=/sauer1/users/Alexis/examples_lcms_workflow/input -e OUTPUT=/sauer1/users/Alexis/examples_lcms_workflow/output -e USERNAME=dalexis adelabriere/lcms_workflow_zamboni:latest
```
with :
* __INPUT__ the input directory, which can be on Sauer1, here
* __OUTPUT__ the output directory which can also be on Sauer1, it should be an empty directory. It can potentially include a *parameters.txt* file
* __USERNAME__ your username to access sauer1 (the same than your windows session login)


###More detail

### What's inside
The docker is focused on the passage form raw-files to a as set of usable informations. The LC-MS workflow extract 2 kind informations, pekas and ms-ms spectra specific of MS-MS spectra.
* A set of peaktable containing all the peaks extracted in the MS1 format one for each .mzML files in a csv format each including the following fields :
  * _mz_ : The measured mass-to-charge ratio measured as the intensity weighted mz across the different scans.
  * _rt_ : The measured retention time at the apex of the peak
  * _height_ : The peak height in count or as an intensity
  * _intensity_ : The integrated area of the peak in the time dimension
  * _rt_min_ : The detected start of the peak in minute
  * _rt_max_ : The detected end of the peak in minute
  * _mz_min_ : The detected end of the peak in minute
  * _mz_max_ : The detected end of the peak in minute
  * _SN_ : The signal-to-noise ratio as measured by the ADAP algorithm
  * _peakwidth_ : The peakwidth of the chromatographic peak calculated as _rt_max - rt_min_
  * _right_on_left_assymetry_ : A measure of the peak assymetry calculated as  _(rt_max - rt)/(rt - rt_min)_
* A set of _.mgf_ containing all the MS-MS spectra in .mgf format. The .mgf format is standard format used by many tools to idetify ms-ms spectra (GNPS spectral search, SIRIUS, CFM-ID).


```
docker run -it --cap-add=SYS_ADMIN --cap-add=DAC_READ_SEARCH --privileged -e INPUT=/sauer1/users/Alexis/examples_lcms_workflow/input -e OUTPUT=/sauer1/users/Alexis/examples_lcms_workflow/output -e USERNAME=dalexis adelabriere/lcms_workflow_zamboni:latest
```


## What is inside this docker ?

The LCMS processing workflow incorporates three main steps :
- Peak picking using the MZmine workflow
- Peak alignment using an in-house aligner
- Peak feature annotations using the MScliques worklow.
- The MS-MS spectra are eventually output to be the majority of the daya. -->
