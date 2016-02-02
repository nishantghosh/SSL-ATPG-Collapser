#!/usr/bin/env python

import cframe
import argparse
import os

def main():

    # Process command line input
    parser = argparse.ArgumentParser(description="Collapse faults in an ISCAS circuit.")
    parser.add_argument("circuit", help="ISCAS file describing circuit to be collapsed")
    parser.add_argument("outfile", help="Base name for output files generated")
    
    args = parser.parse_args()

    # Load circuit
    circ = cframe.Circuit(args.circuit)

    # Print circuit stats
    circ.print_summary()

    # Collapse faults
    collapsed = collapse_circuit(circ)

    # Write out to collapsed fault class file
    with open(args.outfile+".fclass", "w+") as cfile:
        cfile.write("# Fault class tree for %s\n" %(args.circuit))
        for fcs in collapsed:
            fcs.write(cfile)
            cfile.write("\n")

    # Order faults
    ordered = []
    dom = []
    for fcs in collapsed:
        order(fcs, ordered)

    # Print out ordered faults to file
    with open(args.outfile+".order", "w+") as ofile:
        for num, fcs in enumerate(ordered):
            ofile.write("%s: %s\n" %(str(num+1).rjust(5), str(fcs.equivalent[0])))

    # Note: you will need to create your own function, call it (probably from here),
    # and properly write the results to a file if you choose to do the extra credit.
    #print("TODO: dominated_not_dominating extra credit (if desired).")
    
           
       
        

def collapse_circuit(circ):
    """Collapse all of the faults present in a cframe Circuit object."""

    top_fcs = []   # List of all top-level fault classes
    gate_queue = set()   # Set of gate names that need to be processed

    circ.reset_flags()

    # Start processing circuit from the outputs
    for gname in circ.outputs:
        gate_queue.add(gname)

    # Process gates one at time
    while len(gate_queue) > 0:

        # print(gate_queue)
        gname = gate_queue.pop()

        if circ.gatemap[gname].flag:
            #print(circ.gatemap[gname])
            continue
        print(" Gate Queue: ", gate_queue)
        # Process SA0 fault
        sa0 = cframe.Fault(cframe.Roth.Zero, gname)
        fclass_sa0 = cframe.FaultClass(sa0)
        top_fcs.append(fclass_sa0)
        gate_queue.update(collapse_fault(sa0, fclass_sa0, top_fcs, circ))
        print(" Gate Queue: ", gate_queue)

        # Process SA1 fault
        sa1 = cframe.Fault(cframe.Roth.One, gname)
        fclass_sa1 = cframe.FaultClass(sa1)
        top_fcs.append(fclass_sa1)
        gate_queue.update(collapse_fault(sa1, fclass_sa1, top_fcs, circ))
        print(" Gate Queue: ", gate_queue)

        # Mark gate as processed
        circ.gatemap[gname].flag = True

    return top_fcs

def collapse_fault(flt, fltclass, top_fcs, circ):
    """Collapse single fault in a cframe Circuit object"""
    ret = set()
    rothv = flt.value
    fanin = []
    name = "" 
    # Get gate type and list of fan-in
    for gate in circ.gatemap.values():
       if flt.stem == gate.name: 
          name = gate.gatetype
          fanin = gate.fanin

    # Check if net is a branch
    def is_branch(fanin, circ):
      count = 0
      for gate in circ.gatemap.values():
         for fin in gate.fanin:
            if fanin == fin:
               count += 1
      if count > 1:
         return 1
      else: 
         return 0

    # Get gate object from Circuit class
    def find_gate(stem, circ):
       for gate in circ.gatemap.values():
          if stem == gate.name:
             return gate

    """ Collapse fault for different types of gates """
    if name == "AND":
       if rothv == cframe.Roth.Zero:
         for i in fanin:
            if(is_branch(i, circ)):
               sa0 = cframe.Fault(cframe.Roth.Zero, i, flt.stem)
               fltclass.add_equivalent(sa0)
               ret.add(i)
            else:
               sa0 = cframe.Fault(cframe.Roth.Zero, i)
               fltclass.add_equivalent(sa0)
               ret.update(collapse_fault(sa0, fltclass, top_fcs, circ))
               
       else:
         for i in fanin:
            if(is_branch(i, circ)):
               sa1 = cframe.Fault(cframe.Roth.One, i, flt.stem)
               fltclass_sa = cframe.FaultClass(sa1)
               fltclass.add_dominated(fltclass_sa)
               ret.add(i)
            else:
               sa1 = cframe.Fault(cframe.Roth.One, i)
               fltclass_sa = cframe.FaultClass(sa1)
               ret.update(collapse_fault(sa1,fltclass_sa,top_fcs,circ))
               fltclass.add_dominated(fltclass_sa)

    elif name == "NAND":
       if rothv == cframe.Roth.Zero:
         for i in fanin:
            if(is_branch(i, circ)):
               sa1 = cframe.Fault(cframe.Roth.One, i, flt.stem)
               fltclass_sa = cframe.FaultClass(sa1)
               fltclass.add_dominated(fltclass_sa)
               ret.add(i)
               
            else:
               sa1 = cframe.Fault(cframe.Roth.One, i)
               fltclass_sa = cframe.FaultClass(sa1)
               ret.update(collapse_fault(sa1,fltclass_sa,top_fcs,circ))
               fltclass.add_dominated(fltclass_sa)
       else:
         for i in fanin:
            if(is_branch(i, circ)):
               sa0 = cframe.Fault(cframe.Roth.Zero, i, flt.stem)
               fltclass.add_equivalent(sa0)
               ret.add(i)
            else:
               sa0 = cframe.Fault(cframe.Roth.Zero, i)
               fltclass.add_equivalent(sa0)    
               ret.update(collapse_fault(sa0, fltclass, top_fcs, circ))
               

    elif name == "OR":
       if rothv == cframe.Roth.Zero:
         for i in fanin:
            if(is_branch(i, circ)):
               sa0 = cframe.Fault(cframe.Roth.Zero, i, flt.stem)
               fltclass_sa = cframe.FaultClass(sa0)
               fltclass.add_dominated(fltclass_sa)
               ret.add(i)
            else:
               sa0 = cframe.Fault(cframe.Roth.Zero, i)
               fltclass_sa = cframe.FaultClass(sa0)
               ret.update(collapse_fault(sa0, fltclass_sa, top_fcs, circ))
               fltclass.add_dominated(fltclass_sa)  
       else:
         for i in fanin:
            if(is_branch(i, circ)):
               sa1 = cframe.Fault(cframe.Roth.One, i, flt.stem)
               fltclass.add_equivalent(sa1)
               ret.add(i)
            else:
               sa1 = cframe.Fault(cframe.Roth.One, i)
               fltclass.add_equivalent(sa1)    
               ret.update(collapse_fault(sa1, fltclass, top_fcs, circ))

    elif name == "NOR":
       if rothv == cframe.Roth.One:
         for i in fanin:
            if(is_branch(i, circ)):
               sa0 = cframe.Fault(cframe.Roth.Zero, i, flt.stem)
               fltclass_sa = cframe.FaultClass(sa0)
               fltclass.add_dominated(fltclass_sa)
               ret.add(i)
            else:
               sa0 = cframe.Fault(cframe.Roth.Zero, i)
               fltclass_sa = cframe.FaultClass(sa0)
               ret.update(collapse_fault(sa0, fltclass_sa, top_fcs, circ))
               fltclass.add_dominated(fltclass_sa)  
       else:
         for i in fanin:
            if(is_branch(i, circ)):
               sa1 = cframe.Fault(cframe.Roth.One, i, flt.stem)
               fltclass.add_equivalent(sa1)
               ret.add(i)
            else:
               sa1 = cframe.Fault(cframe.Roth.One, i)
               fltclass.add_equivalent(sa0)    
               ret.update(collapse_fault(sa1, fltclass, top_fcs, circ))

    elif name == "NOT":
       if rothv == cframe.Roth.Zero:
         for i in fanin:
            if(is_branch(i,circ)):
              sa1 = cframe.Fault(cframe.Roth.One, i, flt.stem)
              fltclass.add_equivalent(sa1)
              ret.add(i)
            else:
              sa1 = cframe.Fault(cframe.Roth.One, i)
              fltclass.add_equivalent(sa1)
              if(i not in circ.inputs):
                 ret.update(collapse_fault(sa1, fltclass, top_fcs, circ))
       else:
         for i in fanin:
            if(is_branch(i,circ)):
              sa0 = cframe.Fault(cframe.Roth.Zero, i, flt.stem)
              fltclass.add_equivalent(sa0)
              ret.add(i)
            else:
              sa0 = cframe.Fault(cframe.Roth.Zero, i)
              fltclass.add_equivalent(sa0)
              if(i not in circ.inputs):
                 ret.update(collapse_fault(sa0, fltclass, top_fcs, circ))

    elif name == "BUFF":
       if rothv == cframe.Roth.One:
         for i in fanin:
            if(is_branch(i,circ)):
              sa1 = cframe.Fault(cframe.Roth.One, i, flt.stem)
              fltclass.add_equivalent(sa1)
              ret.add(i)
            else:
              sa1 = cframe.Fault(cframe.Roth.One, i)
              fltclass.add_equivalent(sa1)
              if(i not in circ.inputs):
                 ret.update(collapse_fault(sa1, fltclass, top_fcs, circ))
       else:
         for i in fanin:
            if(is_branch(i,circ)):
              sa0 = cframe.Fault(cframe.Roth.Zero, i, flt.stem)
              fltclass.add_equivalent(sa0)
              ret.add(i)
            else:
              sa0 = cframe.Fault(cframe.Roth.Zero, i)
              fltclass.add_equivalent(sa0)
              if(i not in circ.inputs):
                 ret.update(collapse_fault(sa0, fltclass, top_fcs, circ))

    elif name == "XOR":
       for i in fanin:
          if(is_branch(i, circ)):
            sa0 = cframe.Fault(cframe.Roth.Zero, i, flt.stem)
            sa1 = cframe.Fault(cframe.Roth.One, i, flt.stem)
            fclass_sa0 = cframe.FaultClass(sa0)
            fclass_sa1 = cframe.FaultClass(sa1)
            top_fcs.append(fclass_sa0)
            top_fcs.append(fclass_sa1)

          else:
            ret.add(i)

    elif name == "XNOR":
       for i in fanin:
          if(is_branch(i, circ)):
            sa0 = cframe.Fault(cframe.Roth.Zero, i, flt.stem)
            sa1 = cframe.Fault(cframe.Roth.One, i, flt.stem)
            fclass_sa0 = cframe.FaultClass(sa0)
            fclass_sa1 = cframe.FaultClass(sa1)
            top_fcs.append(fclass_sa0)
            top_fcs.append(fclass_sa1)
          else:
            ret.add(i)
    
    elif name == "INPUT":
       if(is_branch(flt.stem, circ)):
          ret.add(flt.stem)
    
											
    return ret

def order(fltclass, ordered):
    
    if(fltclass.dominated != []):
      for cls in fltclass.dominated:
        order(cls, ordered)
    
    ordered.append(fltclass)

   
    
    #print("TODO: Complete this function to put all fault classes in order into the \"ordered\" list provided.")


if __name__ == '__main__':

    # Open logging file
    logfile = os.path.join(os.path.dirname(__file__), "logs/collapser.log")
    cframe.logging.basicConfig(filename=logfile,
                               format='%(asctime)s %(message)s',
                               datefmt='%m/%d/%Y %I:%M:%S %p',
                               level=cframe.logging.DEBUG)

    # Run main function
    main()
