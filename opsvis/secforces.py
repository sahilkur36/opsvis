import openseespy.opensees as ops
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from matplotlib.collections import PolyCollection
from matplotlib.patches import Circle, Polygon, Wedge
from matplotlib.animation import FuncAnimation
import matplotlib.tri as tri

from settings import *
import model


def section_force_distribution_2d(ex, ey, pl, nep=2,
                                  ele_load_data=[['-beamUniform', 0., 0.]]):
    """
    Calculate section forces (N, V, M) for an elastic 2D Euler-Bernoulli beam.

    Input:
    ex, ey - x, y element coordinates in global system
    nep - number of evaluation points, by default (2) at element ends
    ele_load_list - list of transverse and longitudinal element load
      syntax: [ele_load_type, Wy, Wx]
      For now only '-beamUniform' element load type is acceptable

    Output:
    s = [N V M]; shape: (nep,3)
        section forces at nep points along local x
    xl: coordinates of local x-axis; shape: (nep,)

    Use it with dia_sf to draw N, V, M diagrams.

    nep : int
        number of evaluation points, by default (2) at element ends
        If the element load is between the points then nep is increased by 1 or 2

    TODO: add '-beamPoint' element load type
    """


    Lxy = np.array([ex[1]-ex[0], ey[1]-ey[0]])
    L = np.sqrt(Lxy @ Lxy)

    nlf = len(pl)
    xl = np.linspace(0., L, nep)
    one = np.ones(nep)


    for ele_load_data_i in ele_load_data:
        ele_load_type = ele_load_data_i[0]

        if nlf == 1:  # trusses
            N_1 = pl[0]
        elif nlf == 6:  # plane frames
            # N_1, V_1, M_1 = pl[0], pl[1], pl[2]
            N_1, V_1, M_1 = pl[:3]
        else:
            print('\nWarning! Not supported. Number of nodal forces: {nlf}')

        if ele_load_type == '-beamUniform':
            # raise ValueError
            # raise NameError

            n_ele_load_data = len(ele_load_data_i)

            if n_ele_load_data == 3:
                # eload_type, Wy, Wx = ele_load_data[0], ele_load_data[1], ele_load_data[2]
                Wy, Wx = ele_load_data_i[1], ele_load_data_i[2]

                if nlf == 6:
                    s = np.zeros((nep, 3))
                elif nlf == 1:
                    s = np.zeros((nep, 1))

                N = -1.*(N_1 * one + Wx * xl)

                if nlf == 6:
                    V = V_1 * one + Wy * xl
                    M = -M_1 * one + V_1 * xl + 0.5 * Wy * xl**2
                    s += np.column_stack((N, V, M))
                elif nlf == 2:
                    s += np.column_stack((N))

            elif n_ele_load_data == 7:
                wta, waa, aL, bL, wtb, wab = ele_load_data_i[1:7]
                a, b = aL*L, bL*L

                bma = b - a

                if a in xl:
                    pass
                else:
                    xl = np.insert(xl, xl.searchsorted(a), a)
                    nep += 1
                if b in xl:
                    pass
                else:
                    xl = np.insert(xl, xl.searchsorted(b), b)
                    nep += 1

                if nlf == 6:
                    s = np.zeros((nep, 3))
                elif nlf == 2:
                    s = np.zeros((nep, 1))


                indx = 0
                for x in np.nditer(xl):
                    xma = x - a
                    wtx = wta + (wtb - wta) * xma / bma
                    # xc = a + bma * (wtb + 2*wta) / (3 * (wta + wtb))
                    if wtx == 0:
                        xc = 0.
                    else:
                        xc = a + xma * (wtx + 2*wta) / (3 * (wta + wtx))

                    Ax = 0.5 * (wtx+wta) * xma
                    V1x = V_1 * x
                    Axxc = Ax * xc

                    if x < a:
                        pass
                    elif x >= a and x <= b:
                        s[indx, 0] = -1.*(N_1 + (wab - waa) * x)
                        s[indx, 1] = V_1 + Ax
                        s[indx, 2] = -M_1 + V1x + Axxc

                    elif x > b:
                        pass

                    indx += 1

                if aL == 0 and bL == 0:
                    N = -1.*(N_1 * one + wta * xl)
                    V = V_1 * one + wta * xl
                else:
                    N = 0

        elif ele_load_type == '-beamPoint':
            Pt, aL, Pa = ele_load_data_i[1:4]
            a = aL*L

            if a in xl:
                # idx = xl.searchsorted(a)
                # np.concatenate((xl[:idx], [a], xl[idx:]))
                xl = np.insert(xl, xl.searchsorted(a+0.001), a+0.001)
                nep += 1

            else:
                # idx = xl.searchsorted(a)
                # xl = np.concatenate((xl[:idx], [a], xl[idx:]))
                # idx = xl.searchsorted(a+0.001)
                # xl = np.concatenate((xl[:idx], [a+0.001], xl[idx:]))
                xl = np.insert(xl, xl.searchsorted(a), a)
                xl = np.insert(xl, xl.searchsorted(a+0.001), a+0.001)
                nep += 2

            if nlf == 6:
                s = np.zeros((nep, 3))
            elif nlf == 2:
                s = np.zeros((nep, 1))


            indx = 0
            for x in np.nditer(xl):
                if x <= a:
                    s[indx, 0] = -1. * N_1
                    s[indx, 1] = V_1
                    s[indx, 2] = -M_1 + V_1 * x
                elif x > a:
                    s[indx, 0] = -1. * (N_1 + Pa)
                    s[indx, 1] = V_1 + Pt
                    s[indx, 2] = -M_1 + V_1 * x + Pt * (x-a)

                indx += 1


    # if eload_type == '-beamUniform':
    # else:

    return s, xl, nep


def section_force_distribution_3d(ex, ey, ez, pl, nep=2,
                                  ele_load_data=['-beamUniform', 0., 0., 0.]):
    """
    Calculate section forces (N, Vy, Vz, T, My, Mz) for an elastic 3d beam.

    Longer description

    Parameters
    ----------

    ex : list
        x element coordinates
    ey : list
        y element coordinates
    ez : list
        z element coordinates
    pl : ndarray
    nep : int
        number of evaluation points, by default (2) at element ends

    ele_load_list : list
        list of transverse and longitudinal element load
        syntax: [ele_load_type, Wy, Wz, Wx]
        For now only '-beamUniform' element load type is acceptable.

    Returns
    -------

    s : ndarray
        [N Vx Vy T My Mz]; shape: (nep,6)
        column vectors of section forces along local x-axis

    uvwfi : ndarray
        [u v w fi]; shape (nep,4)
        displacements at nep points along local x

    xl : ndarray
        coordinates of local x-axis; shape (nep,)

    nep : int
        number of evaluation points, by default (2) at element ends
        If the element load is between the points then nep is increased by 1 or 2

    Notes
    -----

    Todo: add '-beamPoint' element load type

    """

    # eload_type = ele_load_data[0]
    Wy, Wz, Wx = ele_load_data[1], ele_load_data[2], ele_load_data[3]

    N1, Vy1, Vz1, T1, My1, Mz1 = pl[:6]

    Lxyz = np.array([ex[1]-ex[0], ey[1]-ey[0], ez[1]-ez[0]])
    L = np.sqrt(Lxyz @ Lxyz)

    xl = np.linspace(0., L, nep)
    one = np.ones(nep)

    N = -1.*(N1*one + Wx*xl)
    Vy = Vy1*one + Wy*xl
    Vz = Vz1*one + Wz*xl
    T = -T1*one
    Mz = -Mz1*one + Vy1*xl + 0.5*Wy*xl**2
    My = My1*one + Vz1*xl + 0.5*Wz*xl**2

    s = np.column_stack((N, Vy, Vz, T, My, Mz))

    return s, xl


def section_force_diagram_2d(sf_type, sfac=1., nep=17,
                             fmt_secforce1=fmt_secforce1,
                             fmt_secforce2=fmt_secforce2,
                             fig_wi_he=False, fig_lbrt=False,
                             ref_vert_lines=True,
                             end_max_values=True,
                             node_supports=True, ax=False):
    """Display section forces diagram for 2d beam column model.

    This function plots a section forces diagram for 2d beam column elements
    with or without element loads. For now only '-beamUniform' constant
    transverse or axial element loads are supported.

    Args:
        sf_type (str): type of section force: 'N' - normal force,
            'V' - shear force, 'M' - bending moments.

        sfac (float): scale factor by wich the values of section forces are
            multiplied.

        nep (int): number of evaluation points including both end nodes
            (default: 17)

        fmt_secforce1 (dict): line format dictionary for section force distribution
            curve.

        fmt_secforce2 (dict): line format dictionary for auxiliary reference lines.

        fig_wi_he (tuple): contains width and height of the figure

        fig_lbrt (tuple): a tuple contating left, bottom, right and top offsets

        ref_vert_lines (bool): True means plot the vertical reference lines
            on the section force diagrams.

        end_max_values (bool): True means show the values at element ends and
            extreme (max, min) value between the ends.

        node_supports (bool): True - show the supports.
            Default: True.

        ax: axis object.
    Usage:
        See example: demo_portal_frame.py
    """

    if not ax:
        if fig_wi_he:
            fig_wi, fig_he = fig_wi_he
            fig, ax = plt.subplots(figsize=(fig_wi/2.54, fig_he/2.54))
        else:
            fig, ax = plt.subplots()

        if fig_lbrt:
            fleft, fbottom, fright, ftop = fig_lbrt
            fig.subplots_adjust(left=fleft, bottom=fbottom, right=fright, top=ftop)

    # model
    model.plot_model(node_labels=0, element_labels=0, fmt_model=fmt_model_secforce,
                     node_supports=False, ax=ax)

    maxVal, minVal = -np.inf, np.inf
    ele_tags = ops.getEleTags()

    Ew = model.get_Ew_data_from_ops_domain()

    for ele_tag in ele_tags:

        ele_class_tag = ops.getEleClassTags(ele_tag)[0]

        if (ele_class_tag == EleClassTag.ElasticBeam2d or
            ele_class_tag == EleClassTag.ForceBeamColumn2d or
            ele_class_tag == EleClassTag.DispBeamColumn2d or
            ele_class_tag == EleClassTag.truss):

            nd1, nd2 = ops.eleNodes(ele_tag)

            # element x, y coordinates
            ex = np.array([ops.nodeCoord(nd1)[0],
                           ops.nodeCoord(nd2)[0]])
            ey = np.array([ops.nodeCoord(nd1)[1],
                           ops.nodeCoord(nd2)[1]])

            Lxy = np.array([ex[1]-ex[0], ey[1]-ey[0]])
            L = np.sqrt(Lxy @ Lxy)
            cosa, cosb = Lxy / L

            if ele_class_tag == EleClassTag.truss:
                axial_force = ops.eleResponse(ele_tag, 'axialForce')[0]
                ss = -axial_force * np.ones(nep)
                xl = np.linspace(0., L, nep)

                if axial_force > 0:
                    va = 'top'
                    fmt_color = 'b'
                    fmt_secforce1 = fmt_secforce_tension
                else:
                    va = 'bottom'
                    fmt_color = 'r'
                    fmt_secforce1 = fmt_secforce_compression

            else:
                # by default no element load
                eload_data = [['-beamUniform', 0., 0.]]
                if ele_tag in Ew:
                    eload_data = Ew[ele_tag]

                pl = ops.eleResponse(ele_tag, 'localForces')

                s_all, xl, nep = section_force_distribution_2d(ex, ey, pl, nep, eload_data)

                if sf_type == 'N' or sf_type == 'axial':
                    ss = s_all[:, 0]
                elif sf_type == 'V' or sf_type == 'shear' or sf_type == 'T':
                    ss = s_all[:, 1]
                elif sf_type == 'M' or sf_type == 'moment':
                    ss = s_all[:, 2]


            # minVal = min(minVal, np.min(ss))
            # maxVal = max(maxVal, np.max(ss))
            minVal, minVal_ind = np.amin(ss), np.argmin(ss)
            maxVal, maxVal_ind = np.amax(ss), np.argmax(ss)

            s = ss * sfac

            s_0 = np.zeros((nep, 2))
            s_0[0, :] = [ex[0], ey[0]]

            s_0[1:, 0] = s_0[0, 0] + xl[1:] * cosa
            s_0[1:, 1] = s_0[0, 1] + xl[1:] * cosb

            s_p = np.copy(s_0)

            # positive M are opposite to N and V
            if sf_type == 'M' or sf_type == 'moment':
                s *= -1.

            s_p[:, 0] -= s * cosb
            s_p[:, 1] += s * cosa

            ax.axis('equal')

            # section force curve
            ax.plot(s_p[:, 0], s_p[:, 1], **fmt_secforce1)

            # reference perpendicular lines
            if ref_vert_lines:
                for i in np.arange(nep):
                    ax.plot([s_0[i, 0], s_p[i, 0]], [s_0[i, 1], s_p[i, 1]],
                            **fmt_secforce2)
            else:
                ax.plot([s_0[0, 0], s_p[0, 0]], [s_0[0, 1], s_p[0, 1]],
                        **fmt_secforce2)
                ax.plot([s_0[-1, 0], s_p[-1, 0]], [s_0[-1, 1], s_p[-1, 1]],
                        **fmt_secforce2)

            if ele_class_tag == EleClassTag.truss:
                ha = 'center'
                ax.text(s_p[int(nep / 2), 0], s_p[int(nep / 2), 1],
                        f'{abs(axial_force):.1f}', va=va, ha=ha, color=fmt_color)
            else:
                if end_max_values:
                    ha = 'left'
                    va = 'bottom'
                    ax.text(s_p[0, 0], s_p[0, 1],
                            f'{ss[0]:.5g}', va=va, ha=ha)
                    ax.text(s_p[-1, 0], s_p[-1, 1],
                            f'{ss[-1]:.5g}', va=va, ha=ha)

                    if minVal_ind != 0 or minVal_ind != nep - 1:
                        ax.text(s_p[minVal_ind, 0], s_p[minVal_ind, 1],
                                f'{ss[minVal_ind]:.5g}', va=va, ha=ha)

                    if maxVal_ind != 0 or maxVal_ind != nep - 1:
                        ax.text(s_p[maxVal_ind, 0], s_p[maxVal_ind, 1],
                                f'{ss[maxVal_ind]:.5g}', va=va, ha=ha)

    if node_supports:
        node_tags = ops.getNodeTags()
        model._plot_supports(node_tags, ax)

    # ax.grid(False)

    return minVal, maxVal


def section_force_diagram_3d(sf_type, Ew, sfac=1., nep=17,
                             fmt_secforce1=fmt_secforce1,
                             fmt_secforce2=fmt_secforce2,
                             ref_vert_lines=True,
                             end_max_values=True,
                             dir_plt=0, ax=False):
    """Display section forces diagram of a 3d beam column model.

    This function plots section forces diagrams for 3d beam column elements
    with or without element loads. For now only '-beamUniform' constant
    transverse or axial element loads are supported.

    Args:
        sf_type (str): type of section force: 'N' - normal force,
            'Vy' or 'Vz' - shear force, 'My' or 'Mz' - bending moments,
            'T' - torsional moment.

        Ew (dict): Ew Python dictionary contains information on non-zero
            element loads, therfore each item of the Python dictionary
            is in the form: 'ele_tag: ['-beamUniform', Wy, Wz, Wx]'.

        sfac (float): scale factor by wich the values of section forces are
            multiplied.

        nep (int): number of evaluation points including both end nodes
            (default: 17)

        fmt_secforce1 (dict): line format dictionary for section force distribution
            curve.

        fmt_secforce2 (dict): line format dictionary for auxiliary reference lines.

        end_max_values (bool): True means show the values at element ends and
            extreme (max, min) value between the ends.

        dir_plt {0, 1, 2}: direction in which to plot the load effects:
            0 (default) - as defined in the code for each load effect type
            1 - in the y-axis (default for N, Vy, T, Mz)
            2 - in the z-axis (default for Vz, My)

    Usage:
        See example: demo_cantilever_3el_3d.py

    Todo:

    Add support for other element loads available in OpenSees: partial
    (trapezoidal) uniform element load, and 'beamPoint' element load.
    """

    maxVal, minVal = -np.inf, np.inf
    ele_tags = ops.getEleTags()

    azim, elev = az_el
    fig_wi, fig_he = fig_wi_he
    fleft, fbottom, fright, ftop = fig_lbrt

    fig = plt.figure(figsize=(fig_wi/2.54, fig_he/2.54))
    fig.subplots_adjust(left=.08, bottom=.08, right=.985, top=.94)

    ax = fig.add_subplot(111, projection=Axes3D.name)
    # ax.axis('equal')

    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')

    ax.view_init(azim=azim, elev=elev)

    for i, ele_tag in enumerate(ele_tags):

        # by default no element load
        eload_data = ['-beamUniform', 0., 0., 0.]
        if ele_tag in Ew:
            eload_data = Ew[ele_tag]

        nd1, nd2 = ops.eleNodes(ele_tag)

        # element x, y coordinates
        ex = np.array([ops.nodeCoord(nd1)[0],
                       ops.nodeCoord(nd2)[0]])
        ey = np.array([ops.nodeCoord(nd1)[1],
                       ops.nodeCoord(nd2)[1]])
        ez = np.array([ops.nodeCoord(nd1)[2],
                       ops.nodeCoord(nd2)[2]])

        # eo = Eo[i, :]
        xloc = ops.eleResponse(ele_tag, 'xlocal')
        yloc = ops.eleResponse(ele_tag, 'ylocal')
        zloc = ops.eleResponse(ele_tag, 'zlocal')
        g = np.vstack((xloc, yloc, zloc))

        G, _ = model.rot_transf_3d(ex, ey, ez, g)

        g = G[:3, :3]

        pl = ops.eleResponse(ele_tag, 'localForces')

        s_all, xl = section_force_distribution_3d(ex, ey, ez, pl, nep,
                                                  eload_data)

        # 1:'y' 2:'z'
        if sf_type == 'N':
            ss = s_all[:, 0]
            dir_plt_tmp = 1
        elif sf_type == 'Vy':
            ss = s_all[:, 1]
            dir_plt_tmp = 1
        elif sf_type == 'Vz':
            ss = s_all[:, 2]
            dir_plt_tmp = 2
        elif sf_type == 'T':
            ss = s_all[:, 3]
            dir_plt_tmp = 1
        elif sf_type == 'My':
            ss = s_all[:, 4]
            dir_plt_tmp = 2
        elif sf_type == 'Mz':
            ss = s_all[:, 5]
            dir_plt_tmp = 1

        if dir_plt == 0:
            dir_plt = dir_plt_tmp

        # minVal = min(minVal, np.min(ss))
        # maxVal = max(maxVal, np.max(ss))
        minVal, minVal_ind = np.amin(ss), np.argmin(ss)
        maxVal, maxVal_ind = np.amax(ss), np.argmax(ss)

        s = ss * sfac

        # FIXME - can be simplified
        s_0 = np.zeros((nep, 3))
        s_0[0, :] = [ex[0], ey[0], ez[0]]

        s_0[1:, 0] = s_0[0, 0] + xl[1:] * g[0, 0]
        s_0[1:, 1] = s_0[0, 1] + xl[1:] * g[0, 1]
        s_0[1:, 2] = s_0[0, 2] + xl[1:] * g[0, 2]

        s_p = np.copy(s_0)

        # positive M are opposite to N and V
        # if sf_type == 'Mz' or sf_type == 'My':
        if sf_type == 'Mz':
            s *= -1.

        s_p[:, 0] += s * g[dir_plt, 0]
        s_p[:, 1] += s * g[dir_plt, 1]
        s_p[:, 2] += s * g[dir_plt, 2]

        # plt.axis('equal')

        # model
        # plt.plot(ex, ey, ez, 'k-')
        model.plot_model(node_labels=0, element_labels=0, fmt_model=fmt_model_secforce,
                         node_supports=False, ax=ax)

        # section force curve
        ax.plot(s_p[:, 0], s_p[:, 1], s_p[:, 2], **fmt_secforce1)

        # reference perpendicular lines
        if ref_vert_lines:
            for i in np.arange(nep):
                ax.plot([s_0[i, 0], s_p[i, 0]],
                        [s_0[i, 1], s_p[i, 1]],
                        [s_0[i, 2], s_p[i, 2]], **fmt_secforce2)
        else:
            ax.plot([s_0[0, 0], s_p[0, 0]],
                    [s_0[0, 1], s_p[0, 1]],
                    [s_0[0, 2], s_p[0, 2]], **fmt_secforce2)
            ax.plot([s_0[-1, 0], s_p[-1, 0]],
                    [s_0[-1, 1], s_p[-1, 1]],
                    [s_0[-1, 2], s_p[-1, 2]], **fmt_secforce2)

        if end_max_values:
            ha = 'left'
            va = 'bottom'
            ax.text(s_p[0, 0], s_p[0, 1], s_p[0, 2],
                    f'{ss[0]:.5g}', va=va, ha=ha)
            ax.text(s_p[-1, 0], s_p[-1, 1], s_p[-1, 2],
                    f'{ss[-1]:.5g}', va=va, ha=ha)

            if minVal_ind != 0 or minVal_ind != nep - 1:
                ax.text(s_p[minVal_ind, 0], s_p[minVal_ind, 1], s_p[minVal_ind, 2],
                        f'{ss[minVal_ind]:.5g}', va=va, ha=ha)

            if maxVal_ind != 0 or maxVal_ind != nep - 1:
                ax.text(s_p[maxVal_ind, 0], s_p[maxVal_ind, 1], s_p[maxVal_ind, 2],
                        f'{ss[maxVal_ind]:.5g}', va=va, ha=ha)

    return minVal, maxVal
