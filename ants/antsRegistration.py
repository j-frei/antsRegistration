from nipype.interfaces.ants import Registration
import os, shutil
import SimpleITK as sitk

def registerImage(itk_moving,itk_fixed, store_to=None,type="affine",metric="MI",speed="fast",itk_InitialMovingAffTrf=None,itk_InitialFixedAffTrf=None,n_cores=8,verbose=False):
    """
    Perform a registration using ANTs
    :param itk_moving: itk volume moving
    :param itk_fixed: itk volume fixed
    :param store_to: path to directory to store output, deletes tmp directory if defined
    :param type: string, "affine", "rigid", "deformable"
    :param metric: string "CC","MI"
    :param speed: string, "accurate","normal","fast","debug"
    :param itk_InitialMovingAffTrf: itk Transform, moving
    :param itk_InitialFixedAffTrf: itk Transform, fixed
    """

    # prepare environment / path
    main_dir = os.path.abspath(os.path.dirname(__file__))
    path_dir = os.path.join(main_dir,"bin")
    lib_dir = os.path.join(main_dir,"lib")
    tmp_dir = os.path.join(main_dir,"ants_tmp")
    cwd_old = os.getcwd()

    has_ANTs = shutil.which("antsRegistration")
    has_PATH = "PATH" in os.environ
    if has_PATH:
        PATH_old = os.environ["PATH"]
    if not has_ANTs:
        os.environ["PATH"] = (os.environ["PATH"] + os.pathsep if has_PATH else "") + path_dir
        if not shutil.which("antsRegistration"):
            raise Exception("No executable file \"antsRegistration\" in PATH.")

    has_LD_LIBRARY = "LD_LIBRARY_PATH" in os.environ
    if has_LD_LIBRARY:
        LD_LIBRARY_old = os.environ["LD_LIBRARY_PATH"]
    if not has_ANTs:
        os.environ["LD_LIBRARY_PATH"] = (os.environ["LD_LIBRARY_PATH"] + os.pathsep if has_LD_LIBRARY else "") + lib_dir

    has_NUMBERCORES = "ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS" in os.environ
    if has_NUMBERCORES:
        NUMBERCORES_old = os.environ["ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS"]
    os.environ["ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS"] = "{}".format(n_cores)

    # clean tmp directory
    shutil.rmtree(tmp_dir,ignore_errors=True)
    os.mkdir(tmp_dir)

    # write volumes
    moving_path = os.path.join(tmp_dir,"moving.nii.gz")
    fixed_path = os.path.join(tmp_dir,"fixed.nii.gz")
    sitk.WriteImage(itk_moving,moving_path)
    sitk.WriteImage(itk_fixed,fixed_path)

    # write initial transforms
    if itk_InitialFixedAffTrf:
        fixedtrf_path = os.path.join(tmp_dir,"initialfixedtrf.mat")
        sitk.WriteTransform(itk_InitialFixedAffTrf,fixedtrf_path)
    if itk_InitialMovingAffTrf:
        movingtrf_path = os.path.join(tmp_dir,"initialmovingtrf.mat")
        sitk.WriteTransform(itk_InitialMovingAffTrf,movingtrf_path)

    # switch to tmp dir
    os.chdir(tmp_dir)

    # setup registration parameters
    reg = Registration()

    reg.inputs.fixed_image = fixed_path
    reg.inputs.moving_image = moving_path
    reg.num_threads = n_cores

    if itk_InitialFixedAffTrf:
        reg.inputs.initial_fixed_transform = fixedtrf_path
    if itk_InitialMovingAffTrf:
        reg.inputs.initial_moving_transform = movingtrf_path

    # shared settings

    # what does this do?
    reg.inputs.args='--float 0'

    # warped moving image
    reg.inputs.output_warped_image = 'moving_warped.nii.gz'

    # dimensionality
    reg.inputs.dimension = 3
    # output prefix
    reg.inputs.output_transform_prefix = "output_"
    # interpolation
    reg.inputs.interpolation = "Linear"
    # winsorize-image-intensities
    reg.inputs.winsorize_lower_quantile=0.005
    reg.inputs.winsorize_upper_quantile=0.995
    # histogram matching
    reg.inputs.use_histogram_matching = False
    # write-composite-transform
    reg.inputs.write_composite_transform = False

    # convergence
    if speed == "accurate":
        reg.inputs.number_of_iterations = ([[1000, 100, 50,20]])
        reg.inputs.convergence_threshold = [1.e-6]
        reg.inputs.convergence_window_size = [10]

        reg.inputs.shrink_factors = [[8, 4, 3, 1]]
        reg.inputs.sigma_units = ['vox']
        reg.inputs.smoothing_sigmas = [[4, 3, 2, 1]]
    elif speed == "normal":
        reg.inputs.number_of_iterations = ([[100, 50, 10]])
        reg.inputs.convergence_threshold = [1.e-6]
        reg.inputs.convergence_window_size = [10]

        reg.inputs.shrink_factors = [[8, 4, 2]]
        reg.inputs.sigma_units = ['vox']
        reg.inputs.smoothing_sigmas = [[3, 2, 1]]
    elif speed == "fast":
        reg.inputs.number_of_iterations = ([[100, 50]])
        reg.inputs.convergence_threshold = [1.e-6]
        reg.inputs.convergence_window_size = [10]

        reg.inputs.shrink_factors = [[4, 3]]
        reg.inputs.sigma_units = ['vox']
        reg.inputs.smoothing_sigmas = [[3, 2]]
    elif speed == "debug":
        reg.inputs.number_of_iterations = ([[10]])
        reg.inputs.convergence_threshold = [1.e-6]
        reg.inputs.convergence_window_size = [10]

        reg.inputs.shrink_factors = [[4]]
        reg.inputs.sigma_units = ['vox']
        reg.inputs.smoothing_sigmas = [[3]]
    else:
        raise Exception("Parameter speed must be from the list: accurate, normal, fast, debug")

    # metric
    if metric == "MI":
        reg.inputs.metric=["MI"]
        reg.inputs.metric_weight=[1.0]
        reg.inputs.radius_or_number_of_bins=[32]
        reg.inputs.sampling_strategy=['Regular']
        reg.inputs.sampling_percentage=[0.25]
    elif metric == "CC":
        reg.inputs.metric=["MI"]
        reg.inputs.metric_weight=[1.0]
        reg.inputs.radius_or_number_of_bins=[4]
        reg.inputs.sampling_strategy=['None']
        reg.inputs.sampling_percentage=[0.1]
    else:
        raise Exception("Parameter metric must be from the list: MI,CC")

    # type-specific settings
    if type == "affine":
        reg.inputs.transforms = ['Affine']
        reg.inputs.transform_parameters = [(0.1,)]
    elif type == "rigid":
        reg.inputs.transforms = ['Rigid']
        reg.inputs.transform_parameters = [(0.1,)]
    elif type == "deformable":
        reg.inputs.transforms = ['SyN']
        reg.inputs.transform_parameters = [(0.25,)]
    else:
        raise Exception("Parameter type must be from the list: affine, rigid, deformable")

    if verbose:
        print("Using antsRegistration from: {}".format(shutil.which("antsRegistration")))
        print("Executing: {}".format(reg.cmdline))
    # perform ants call (retrieve by reg.cmdline)
    reg.run()

    # reset environment
    if not has_ANTs:
        if has_PATH:
            os.environ["PATH"] = PATH_old
        else:
            del os.environ["PATH"]

        if has_LD_LIBRARY:
            os.environ["LD_LIBRARY_PATH"] = LD_LIBRARY_old
        else:
            del os.environ["LD_LIBRARY_PATH"]

    if has_NUMBERCORES:
        os.environ["ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS"] = NUMBERCORES_old
    else:
        del os.environ["ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS"]

    if type == 'affine':
        #output_trf_path = ["output_0Affine.mat"]
        output_trf_path = reg._list_outputs().get('forward_transforms',["output_0Affine.mat"])
    elif type == 'rigid':
        #output_trf_path = ["output_0Rigid.mat"]
        output_trf_path = reg._list_outputs().get('forward_transforms',["output_0Rigid.mat"])
    elif type == 'deformable':
        #output_trf_path = ["output_0Warp.nii.gz","output_0InverseWarp.nii.gz"]
        output_trf_path = reg._list_outputs().get('forward_transforms',["output_0Warp.nii.gz"])+reg._list_outputs().get('reverse_transforms',["output_0InverseWarp.nii.gz"])

    output_paths_trf = [ os.path.join(tmp_dir,p) for p in output_trf_path]
    warped_path = os.path.join(tmp_dir,'moving_warped.nii.gz')

    # switch back to old cwd
    os.chdir(cwd_old)

    if store_to:
        # copy output files
        moved_output_paths_trf = []
        for tf in output_paths_trf:
            moved = os.path.join(store_to,os.path.basename(tf))
            moved_output_paths_trf.append(moved)
            shutil.copy(tf,moved)

        moved_warped_path = os.path.join(store_to,os.path.basename(warped_path))
        shutil.copy(warped_path,moved_warped_path)

        # clear tmp directory
        shutil.rmtree(tmp_dir)

        if verbose:
            print("Store transform(s) to: {}".format(", ".join(moved_output_paths_trf)))
            print("Store warped volume to: {}".format(", ".join(moved_warped_path)))

        return {
            "transforms_out":moved_output_paths_trf,
            "warpedMovingVolume":moved_warped_path,
            }
    else:
        if verbose:
            print("Store transform(s) to: {}".format(", ".join(output_paths_trf)))
            print("Store warped volume to: {}".format(", ".join(warped_path)))

        return {
        "transforms_out":output_paths_trf,
        "warpedMovingVolume":warped_path,
        }
