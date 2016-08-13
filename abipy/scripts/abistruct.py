#!/usr/bin/env python
"""Script to export/visualize the crystal structure saved in the netcdf files produced by ABINIT."""
from __future__ import unicode_literals, division, print_function, absolute_import

import sys
import os
import argparse

from monty.functools import prof_main
from pprint import pprint
from tabulate import tabulate
from abipy import abilab
from abipy.iotools.visualizer import Visualizer


@prof_main
def main():

    def str_examples():
        return """\
Usage example:
    abistruct.py spglib  filepath             => Read the structure from file and analyze it with spglib.
    abistruct.py convert filepath cif         => Read the structure from file and print CIF file.
    abistruct.py convert filepath abivars     => Print the ABINIT variables defining the structure.
    abistruct.py convert out_HIST abivars     => Read the last structure from the HIST file and
                                                 print the corresponding Abinit variables.
    abistrcut.py kpath filepath               => Read structure from filepath and print Abinit variables for k-path.
    abistruct.py bz filepath                  => Read structure from filepath, plot BZ with matplotlib.
    abistruct.py abisanitize FILE             => Read structure from FILE, call abisanitize, compare structures and save
                                                 "abisanitized" structure to file.
    abistruct.py visualize filepath xcrysden  => Visualize the structure with XcrysDen.
    abistruct.py ipython filepath             => Read structure from filepath and open Ipython terminal.
    abistruct.py pmgdata mp-149               => Get structure from pymatgen database and print its JSON representation.
"""

    def show_examples_and_exit(err_msg=None, error_code=1):
        """Display the usage of the script."""
        sys.stderr.write(str_examples())
        if err_msg: sys.stderr.write("Fatal Error\n" + err_msg + "\n")
        sys.exit(error_code)

    # Parent parser for commands that need to know the filepath
    path_selector = argparse.ArgumentParser(add_help=False)
    path_selector.add_argument('filepath', nargs="?", help="File with the crystalline structure")

    parser = argparse.ArgumentParser(epilog=str_examples(), formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-V', '--version', action='version', version="%(prog)s version " + abilab.__version__)

    spgopt_parser = argparse.ArgumentParser(add_help=False)
    spgopt_parser.add_argument('--symprec', default=1e-3, type=float,
        help="""\
symprec (float): Tolerance for symmetry finding. Defaults to 1e-3,
    which is fairly strict and works well for properly refined
    structures with atoms in the proper symmetry coordinates. For
    structures with slight deviations from their proper atomic
    positions (e.g., structures relaxed with electronic structure
    codes), a looser tolerance of 0.1 (the value used in Materials
    Project) is often needed.""")
    spgopt_parser.add_argument('--angle-tolerance', default=5.0, type=float,
        help="angle_tolerance (float): Angle tolerance for symmetry finding. Default: 5.0")

    # Parent parser for common options.
    copts_parser = argparse.ArgumentParser(add_help=False)
    copts_parser.add_argument('-v', '--verbose', default=0, action='count', # -vv --> verbose=2
                              help='verbose, can be supplied multiple times to increase verbosity')
    copts_parser.add_argument('--loglevel', default="ERROR", type=str,
                              help="set the loglevel. Possible values: CRITICAL, ERROR (default), WARNING, INFO, DEBUG")

    # Create the parsers for the sub-commands
    subparsers = parser.add_subparsers(dest='command', help='sub-command help',
                                       description="Valid subcommands, use command --help for help")

    p_spglib = subparsers.add_parser('spglib', parents=[copts_parser, path_selector, spgopt_parser],
                                      help="Analyze structure with spglib.")

    # Subparser for convert command.
    p_convert = subparsers.add_parser('convert', parents=[copts_parser, path_selector],
                                      help="Convert structure to the specified format.")
    p_convert.add_argument('format', nargs="?", default="cif", type=str,
                           help="Format of the output file (cif, cssr, POSCAR, json, mson, abivars).")

    p_abisanitize = subparsers.add_parser('abisanitize', parents=[copts_parser, path_selector, spgopt_parser],
                                      help="Sanitize structure with abi_sanitize, compare structures and save result to file.")

    # Subparser for ipython.
    p_ipython = subparsers.add_parser('ipython', parents=[copts_parser, path_selector],
                                      help="Open IPython shell for advanced operations on structure object.")

    # Subparser for bz.
    p_bz = subparsers.add_parser('bz', parents=[copts_parser, path_selector],
                                 help="Read structure from file, plot Brillouin zone with matplotlib.")

    # Subparser for bz.
    p_kpath = subparsers.add_parser('kpath', parents=[copts_parser, path_selector],
                             help="Read structure from file, generate k-path for band-structure calculations.")

    # Subparser for visualize command.
    p_visualize = subparsers.add_parser('visualize', parents=[copts_parser, path_selector],
                                        help="Visualize the structure with the specified visualizer")
    p_visualize.add_argument('visualizer', nargs="?", default="xcrysden", type=str, help=("Visualizer name. "
        "List of visualizer supported: %s" % ", ".join(Visualizer.all_visunames())))

    # Subparser for pmgid command.
    p_pmgdata = subparsers.add_parser('pmgdata', parents=[copts_parser],
                                      help="Get structure from the pymatgen database. Requires internet connection and MAPI_KEY")
    p_pmgdata.add_argument("pmgid", type=str, default=None, help="Pymatgen identifier")
    p_pmgdata.add_argument("--mapi-key", default=None, help="Pymatgen MAPI_KEY. Use env variable if not specified.")
    p_pmgdata.add_argument("--endpoint", default="www.materialsproject.org", help="Pymatgen database.")

    # Subparser for animate command.
    p_animate = subparsers.add_parser('animate', parents=[copts_parser, path_selector],
        help="Read structures from HIST or XDATCAR. Print structures in Xrysden AXSF format to stdout")

    # Parse command line.
    try:
        options = parser.parse_args()
    except Exception as exc:
        show_examples_and_exit(error_code=1)

    # loglevel is bound to the string value obtained from the command line argument.
    # Convert to upper case to allow the user to specify --loglevel=DEBUG or --loglevel=debug
    import logging
    numeric_level = getattr(logging, options.loglevel.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError('Invalid log level: %s' % options.loglevel)
    logging.basicConfig(level=numeric_level)

    if options.command == "spglib":
        structure = abilab.Structure.from_file(options.filepath)
        #print(structure.lattice)
        from pymatgen.symmetry.analyzer import SpacegroupAnalyzer
        spgan = SpacegroupAnalyzer(structure)
        spgdata = spgan.get_symmetry_dataset()
        # Get spacegroup number computed by Abinit if available.
        abispg_number = None if structure.spacegroup is None else structure.spacegroup.spgid

        # Print lattice info
        outs = ["Full Formula ({s})".format(s=structure.composition.formula),
                "Reduced Formula: {}".format(structure.composition.reduced_formula)]
        to_s = lambda x: "%0.6f" % x
        outs.append("abc   : " + " ".join([to_s(i).rjust(10)
                                           for i in structure.lattice.abc]))
        outs.append("angles: " + " ".join([to_s(i).rjust(10)
                                           for i in structure.lattice.angles]))
        print("\n".join(outs))

        print("Space group info (note that magnetic symmetries are not taken into account).")
        print("Spacegroup: %s (%s), Hall: %s, Abinit spg_number: %s" % (
             spgan.get_spacegroup_symbol(), spgan.get_spacegroup_number(), spgan.get_hall(), str(abispg_number)))
        print("Crystal_system: %s, Lattice_type: %s, Point_group: %s" % (
            spgan.get_crystal_system(), spgan.get_lattice_type(), spgan.get_point_group()))
        print()

        wickoffs, equivalent_atoms = spgdata["wyckoffs"], spgdata["equivalent_atoms"]
        table = [["Idx", "Symbol", "Reduced_Coords", "Wyck", "EqIdx"]]
        for i, site in enumerate(structure):
            table.append([
                i,
                site.specie.symbol,
                "%.5f %.5f %.5f" % tuple(site.frac_coords),
                "%s" % wickoffs[i],
                "%d" % equivalent_atoms[i],
            ])

        print(tabulate(table, headers="firstrow"))

        # Print entire dataset.
        if options.verbose: pprint(spgdata)

        return 0

    elif options.command == "convert":
        structure = abilab.Structure.from_file(options.filepath)

        if options.format == "abivars":
            print(structure.abi_string)
        else:
            s = structure.convert(format=options.format)
            print(s)

    elif options.command == "abisanitize":
        print("Calling abi_sanitize to get a new structure in which:")
        print("    * Structure is refined.")
        print("    * Reduced to primitive settings.")
        print("    * Lattice vectors are exchanged if the triple product is negative\n")

        structure = abilab.Structure.from_file(options.filepath)
        sanitized = structure.abi_sanitize(symprec=options.symprec, angle_tolerance=options.angle_tolerance,
                                           primitive=True, primitive_standard=False)
        index = [options.filepath, "abisanitized"]
        frame = abilab.frame_from_structures([structure, sanitized], index=index, with_spglib=True)
        print(frame)

        if not options.verbose:
            print("\nUse -v for more info")
        else:
            #print("\nDifference between structures:")
            if len(structure) == len(sanitized):
                table = []
                for line1, line2 in zip(str(structure).splitlines(), str(sanitized).splitlines()):
                    table.append([line1, line2])
                print(str(tabulate(table, headers=["Initial structure", "Abisanitized"])))

            else:
                print("\nInitial structure:")
                print(structure)
                print("\nabisanitized structure:")
                print(sanitized)

        root, basename = os.path.split(options.filepath)
        new_filename = os.path.join(root, "abisanitized_" + basename)
        print("Saving abisanitized structure as %s" % new_filename)
        if os.path.exists(new_filename):
            raise RuntimeError("%s already exists. Cannot overwrite" % new_filename)
        sanitized.to(filename=new_filename)

    elif options.command == "ipython":
        structure = abilab.Structure.from_file(options.filepath)
        print("Invoking Ipython, `structure` object will be available in the Ipython terminal")
        import IPython
        IPython.start_ipython(argv=[], user_ns={"structure": structure})

    elif options.command == "visualize":
        structure = abilab.Structure.from_file(options.filepath)
        structure.visualize(options.visualizer)

    elif options.command == "kpath":
        structure = abilab.Structure.from_file(options.filepath)
        print("# Abinit Structure")
        print(structure.abi_string)
        print("\n# K-path in reduced coordinates:")
        print("# tolwfr 1e-20 iscf -2 getden ??")
        print(" ndivsm 10")
        print(" kptopt", -(len(structure.hsym_kpoints)-1))
        print(" kptbounds")
        for k in structure.hsym_kpoints:
            print("    %.5f  %.5f  %.5f" % tuple(k.frac_coords), "#", k.name)

    elif options.command == "bz":
        structure = abilab.Structure.from_file(options.filepath)
        structure.show_bz()

    elif options.command == "pmgdata":
        # Get the Structure corresponding the a material_id.
        structure = abilab.Structure.from_material_id(options.pmgid, final=True, api_key=options.mapi_key,
                                                      endpoint=options.endpoint)
        # Convert to json and print it.
        s = structure.convert(format="json")
        print(s)

    elif options.command == "animate":
        from abipy.iotools import xsf_write_structure
        filepath = options.filepath

        if any(filepath.endswith(ext) for ext in ("HIST", "HIST.nc")):
            with abilab.abiopen(filepath) as hist:
                structures = hist.structures

        elif "XDATCAR" in filepath:
            from pymatgen.io.vaspio import Xdatcar
            structures = Xdatcar(filepath).structures
            if not structures:
                raise RuntimeError("Your Xdatcar contains only one structure. Due to a bug "
                    "in the pymatgen routine, your structures won't be parsed correctly"
                    "Solution: Add another structure at the end of the file.")

        else:
            raise ValueError("Don't know how to handle file %s" % filepath)

        xsf_write_structure(sys.stdout, structures)

    else:
        raise ValueError("Unsupported command: %s" % options.command)

    return 0


if __name__ == "__main__":
    sys.exit(main())
