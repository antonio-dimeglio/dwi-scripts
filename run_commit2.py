# PYTHON_ARGCOMPLETE_OK
import argparse
import argcomplete
import os
import commit
from commit import trk2dictionary
import amico
from pathlib import Path

SETUP_MARKER = os.path.expanduser('~/.commit2py_setup_done')

def ensure_setup():
    if not os.path.exists(SETUP_MARKER):
        commit.setup()
        with open(SETUP_MARKER, 'w') as f:
            f.write('done')

def run_commit(args):
    ensure_setup()
    output = Path(args.output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    dwi_scheme = str(output / 'DWI.scheme')
    dict_path = str(output / 'dictionary')

    trk2dictionary.run(
        filename_tractogram=args.tractogram,
        filename_peaks=args.peaks,
        TCK_ref_image=args.dwi,
        path_out=dict_path,
        peaks_use_affine=args.peaks_use_affine,
        fiber_shift=0.5 if args.fiber_shift else 0.0,
        n_threads=args.n_threads,
    )

    amico.util.fsl2scheme(args.bvals, args.bvecs, dwi_scheme)

    mit = commit.Evaluation(str(output), '.', 'dictionary')
    mit.set_verbose(3)
    mit.load_data(args.dwi, dwi_scheme)

    mit.set_model('StickZeppelinBall')
    mit.model.set(1.7e-3, [0.51e-3], [1.7e-3, 3.0e-3])
    mit.generate_kernels(regenerate=True)
    mit.load_kernels()

    mit.load_dictionary()
    mit.set_threads(args.n_threads)
    mit.build_operator()
    mit.fit(tol_fun=1e-3, max_iter=1000)
    mit.save_results()



def main():
    ap = argparse.ArgumentParser('run_commit2py')
    ap.add_argument('dwi', help='DWI volume')
    ap.add_argument('tractogram', help='Tractogram file, either .tck or .trk')
    ap.add_argument('peaks', help='Peaks file')
    ap.add_argument('bvals', help='Path to bvals')
    ap.add_argument('bvecs', help='Path to bvecs')
    ap.add_argument('output', help='Output folder')
    ap.add_argument('--n_threads', type=int, default=8, help='Number of threads to use')
    ap.add_argument('--peaks_use_affine', action=argparse.BooleanOptionalAction, default=False)
    ap.add_argument('--fiber_shift', action=argparse.BooleanOptionalAction, default=False)
    argcomplete.autocomplete(ap)
    args = ap.parse_args()
    run_commit(args)

if __name__ == '__main__':
    main()
