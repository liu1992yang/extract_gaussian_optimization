# extract_gaussian_optimization
python script and shell wrapper that extracts optimized or lowest energy structure(if job fails or interrupted)
to new folder and documented the current total electronic energy in a file;  
handles regular batch submission or with checkpoint queue submission.  

### extract_gaussian_opt.py  
This script alone can work with one gaussian.log file to extract one structure  
Example usage: python extract_gaussian_opt.py input.log new_method new_basis  
The output file will be named "input_opted.gjf" in "opted_gjf" directory and optimized energy will be recorded in a opted_structure_energy.txt in the "opted_gjf"  
If optimization failed, the coordinates for the lowest energy structure will be extracted wih old route card to write out to new file as iput_out.gjf  
stored in "not_done" directory. And the filename "input_out" without extension will be stored in "filelist" file within "not_done"

If call extract_gausian_opt.py a couple times within the same wdir, the opted_structure_energy.txt/filelist will append the result line by line

#### Handled Cases:


#### Case not applied:


### extract_wrapper.sh  



