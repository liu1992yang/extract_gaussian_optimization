import os, subprocess, sys


def check_sys_input():
  if len(sys.argv) < 3 :
    print("Usage: python extract_opt_coords.py input.log new_method new_basis" )
    print("The output file name will be input_opted.gjf and optimized energy will be recorded")
    print("If optimization failed, the coordinates for the lowest energy structure will be extracted wih old method/functional to write out to new file as iput_out.gjf.")
    sys.exit(1)
  finput = sys.argv[1]
  new_method = sys.argv[2]
  new_basis = sys.argv[3]
  if not os.path.exists(finput):
    print("The {} file does not exist".format(finput))
    sys.exit(1)
  return finput, new_method, new_basis


def get_charge_multipl(stoi):
  #str stoi: the line contains stoichiometry info
  formula = stoi.strip().split()[1].strip()
  multipl = 1
  if '(' not in formula:
    charge = 0
    return charge, multipl
  info = formula[formula.index('(')+1:-1]
  if ',' not in info:
    charge = info
  else:
    charge, multipl = info.split(',')[0], info.split(',')[1].strip()
  if charge.endswith('+'):
    charge = charge[:-1]
  return charge, multipl  

def select_structure(optimized, all_block):
  assert all_block, "cannot find any structure info"
  if optimized:
    if len(all_block) < 2:
      return backup_opt(all_block[-1])
    else:
      return energy_coords_block(all_block[-2])
  sorted_coords = sorted(list(map(energy_coords_block, all_block)), key = lambda x: float(x[0]))
  return sorted_coords[0]
  
def backup_opt(block_info):
  data_list = block_info.split('\n')
  is_coords = True
  atom_coords = []
  start_idx = 1000000000
  info_chunk_start = -1
  info_chunk_end = -1
  for idx,val in enumerate(data_list):
    if "#" in val:
      info_chunk_start = idx
    if "Standard orientation" in val:
      start_idx = idx + 5
    if idx >= start_idx:
      if val.startswith(' --------'):
        is_coords = False
      if is_coords:
        atom_coords.append(val)
    if "@" in val and info_chunk_start >0:
      info_chunk_end = idx
  if info_chunk_end > info_chunk_start:
    resplit_list = ''.join(data_list[info_chunk_start: info_chunk_end+1]).split('\\')
    energy_line = ''.join([line for line in resplit_list if 'HF' in line])
    energy =  energy_line.split('=')[1].strip()
  assert energy and atom_coords, 'error file'
  return energy, atom_coords

def energy_coords_block(block_info):
  data_list = block_info.split('\n')
  energy = 1000.0 #initial energy with a very large number(usually it's negative)
  is_coords = True
  atom_coords = []
  start_idx = 1000000000
  for idx,val in enumerate(data_list):
    if val.startswith(" SCF Done:") :
      arr = val.split("=")[1].strip().split()
      energy = float(arr[0])
    if "Standard orientation" in val:
      start_idx = idx + 5
    if idx >= start_idx:
      if val.startswith(' --------'):
        is_coords = False
      if is_coords:
        atom_coords.append(val)
  return energy, atom_coords


def extract_coords(all_atom): 
  return [find_coord_info(atom) for atom in all_atom]

def find_coord_info(atom):
  arr = atom.strip().split()
  return CODE.get(arr[1],'X'), arr[3], arr[4], arr[5]


def read_route_card(line, read_old_bool):
  if line.startswith(" #") and not read_old_bool:
    read_old_bool = True
  if read_old_bool and line.startswith(" --------"):
    read_old_bool = False
  return read_old_bool

def read_blocks(finput):
  optimized = False
  all_block = []
  charge, multipl = None, None
  with open(finput, 'r') as fin:
    is_structure = False
    current_block = ""
    # Read chunks by stoichiometry 
    # append each line in after this current_chunk.append(line)
    # until reaches SCF Done, all_block.append(current_chunk),is_structure = False,current_chunk reset = ""
    # or if SCF not found, read everything till the end
    old_route = []
    read_old_route = False
    for line in fin:
      read_old_route = read_route_card(line, read_old_route)  
      if read_old_route:
        old_route.append(line.strip())
      if line.startswith(" Stoichiometry"):
        is_structure = True
        if not (charge and multipl):
          #only need to parse it once to get charge and multiplicity
          charge, multipl = get_charge_multipl(line)
      if is_structure: 
        current_block += line
        if line.startswith(" SCF Done"):
          is_structure = not is_structure
      if not is_structure:
        if current_block:
          all_block.append(current_block)
        current_block = ""
      if "Optimized" in line:
        optimized = True
    if is_structure:
      all_block.append(current_block)
    assert (charge and multipl) != None, 'no charge or multiplicity found'
    energy, struc = select_structure(optimized, all_block)
    coords = extract_coords(struc)
    return optimized, charge, multipl, ''.join(old_route), energy, coords

def read_write_log(finput, new_method, new_basis):
  optimized, charge, multipl, old_route, energy, coords = read_blocks(finput)
  if optimized:
    fn = finput.split('.')[0] + '_opted.gjf'
    target_folder = 'opted_gjf'
    energy_file = 'opted_structure_energy.txt'
    mkfolder(target_folder)
    energy_dir_file = os.path.join(target_folder, energy_file)
    energy_fmode = 'a' if os.path.exists(energy_dir_file) else 'w'
    with open(energy_dir_file,energy_fmode) as fenergy:
      fenergy.write(fn + '\t' + str(energy) + '\n')
    route_card = '#p opt {}/{} scf=(xqc, tight) pop=min'.format(new_method, new_basis)
  else: 
    print(finput + ' not optimized!')
    fn = finput.split('.')[0] + '_out.gjf'
    target_folder = 'not_done'
    mkfolder(target_folder)
    not_done_list = os.path.join(target_folder,'filelist')
    flist_mode = 'a' if os.path.exists(not_done_list) else 'w'
    route_card = old_route.replace('(restart)','')
    with open(not_done_list, flist_mode) as f_flist:
      f_flist.write(fn.replace('.gjf', '') + '\n')
  with open(os.path.join(target_folder, fn),'w') as fout:
    fout.write('''%mem=64gb
%nproc=28       
%Chk={0}
{1}   

{2}

{3}  {4}
'''.format(fn.replace('gjf','chk'), route_card, fn.replace('.gjf', ''), charge, multipl))
    fout.write('\n'.join(['  %s  %16.7f %16.7f %16.7f' % (atom[0],float(atom[1]),float(atom[2]),float(atom[3])) for atom in coords])+'\n\n')

def mkfolder(target):
  if not os.path.exists(target):
    subprocess.call(['mkdir', target])
  else:
    pass

CODE = {"1" : "H", "2" : "He", "3" : "Li", "4" : "Be", "5" : "B", \
"6"  : "C", "7"  : "N", "8"  : "O",  "9" : "F", "10" : "Ne", \
"11" : "Na" , "12" : "Mg" , "13" : "Al" , "14" : "Si" , "15" : "P", \
"16" : "S"  , "17" : "Cl" , "18" : "Ar" , "19" : "K"  , "20" : "Ca", \
"21" : "Sc" , "22" : "Ti" , "23" : "V"  , "24" : "Cr" , "25" : "Mn", \
"26" : "Fe" , "27" : "Co" , "28" : "Ni" , "29" : "Cu" , "30" : "Zn", \
"31" : "Ga" , "32" : "Ge" , "33" : "As" , "34" : "Se" , "35" : "Br", \
"36" : "Kr" , "37" : "Rb" , "38" : "Sr" , "39" : "Y"  , "40" : "Zr", \
"41" : "Nb" , "42" : "Mo" , "43" : "Tc" , "44" : "Ru" , "45" : "Rh", \
"46" : "Pd" , "47" : "Ag" , "48" : "Cd" , "49" : "In" , "50" : "Sn", \
"51" : "Sb" , "52" : "Te" , "53" : "I"  , "54" : "Xe" , "55" : "Cs", \
"56" : "Ba" , "57" : "La" , "58" : "Ce" , "59" : "Pr" , "60" : "Nd", \
"61" : "Pm" , "62" : "Sm" , "63" : "Eu" , "64" : "Gd" , "65" : "Tb", \
"66" : "Dy" , "67" : "Ho" , "68" : "Er" , "69" : "Tm" , "70" : "Yb", \
"71" : "Lu" , "72" : "Hf" , "73" : "Ta" , "74" : "W"  , "75" : "Re", \
"76" : "Os" , "77" : "Ir" , "78" : "Pt" , "79" : "Au" , "80" : "Hg", \
"81" : "Tl" , "82" : "Pb" , "83" : "Bi" , "84" : "Po" , "85" : "At", \
"86" : "Rn" , "87" : "Fr" , "88" : "Ra" , "89" : "Ac" , "90" : "Th", \
"91" : "Pa" , "92" : "U"  , "93" : "Np" , "94" : "Pu" , "95" : "Am", \
"96" : "Cm" , "97" : "Bk" , "98" : "Cf" , "99" : "Es" ,"100" : "Fm", \
"101": "Md" ,"102" : "No" ,"103" : "Lr" ,"104" : "Rf" ,"105" : "Db", \
"106": "Sg" ,"107" : "Bh" ,"108" : "Hs" ,"109" : "Mt" ,"110" : "Ds", \
"111": "Rg" ,"112" : "Uub","113" : "Uut","114" : "Uuq","115" : "Uup", \
"116": "Uuh","117" : "Uus","118" : "Uuo"}

if __name__ == '__main__':
  finput, new_method, new_basis = check_sys_input() 
  read_write_log(finput,new_method, new_basis)
  sys.exit(0) 


  
