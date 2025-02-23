"""Collection of Pose Conversion Functions to Quaternion Pose Format"""

# global
import ivy

# local
from ivy_mech.orientation import quaternion as ivy_quat
from ivy_mech.pose import matrix_pose as ivy_mat_pose


def axis_angle_pose_to_quaternion_pose(axis_angle_pose):
    """Convert axis-angle pose :math:`\mathbf{p}_{aa} = [\mathbf{x}_c, \mathbf{e}, θ] = [x, y, z, e_x, e_y, e_z, θ]`
    to quaternion pose :math:`\mathbf{p}_{q} = [\mathbf{x}_c, \mathbf{q}] = [x, y, z, q_i, q_j, q_k, q_r]`.

    Parameters
    ----------
    axis_angle_pose
        Axis-angle pose *[batch_shape,7]*

    Returns
    -------
    ret
        Quaternion pose *[batch_shape,7]*

    """

    # BS x 3
    translation = axis_angle_pose[..., :3]

    # BS x 7
    return ivy.concat(
        [translation, ivy_quat.axis_angle_to_quaternion(axis_angle_pose[..., 3:])],
        axis=-1,
    )


def mat_pose_to_quaternion_pose(matrix):
    """Convert matrix pose :math:`\mathbf{P}\in\mathbb{R}^{3×4}` to quaternion pose
    :math:`\mathbf{p}_{q} = [\mathbf{x}_c, \mathbf{q}] = [x, y, z, q_i, q_j, q_k, q_r]`.\n
    `[reference] <http://www.euclideanspace.com/maths/geometry/rotations/conversions/matrixToQuaternion/>`_

    Parameters
    ----------
    matrix
        Matrix pose *[batch_shape,3,4]*

    Returns
    -------
    ret
        Quaternion pose *[batch_shape,7]*

    """

    # BS x 7
    return ivy.concat(
        [matrix[..., 0:3, -1], ivy_quat.rot_mat_to_quaternion(matrix[..., 0:3, 0:3])],
        axis=-1,
    )


def euler_pose_to_quaternion_pose(euler_pose, convention="zyx", batch_shape=None):
    """Convert :math: Euler angle pose
    :math:`\mathbf{p}_{abc} = [\mathbf{x}_c, \mathbf{θ}_{xyz}] = [x, y, z, ϕ_a, ϕ_b, ϕ_c]` to quaternion pose
    :math:`\mathbf{p}_{q} = [\mathbf{x}_c, \mathbf{q}] = [x, y, z, q_i, q_j, q_k, q_r]`.\n
    `[reference] <http://www.euclideanspace.com/maths/geometry/rotations/conversions/matrixToQuaternion/>`_

    Parameters
    ----------
    euler_pose
        Euler angle pose *[batch_shape,6]*
    convention
        The axes for euler rotation, in order of L.H.S. matrix multiplication. (Default value = 'zyx')
    batch_shape
        Shape of batch. Inferred from inputs if None. (Default value = None)

    Returns
    -------
    ret
        Quaternion pose *[batch_shape,7]*

    """

    if batch_shape is None:
        batch_shape = euler_pose.shape[:-1]

    # BS x 7
    return mat_pose_to_quaternion_pose(
        ivy_mat_pose.euler_pose_to_mat_pose(euler_pose, convention, batch_shape)
    )


def increment_quaternion_pose_with_velocity(quat_pose, quat_vel, delta_t):
    """Increment a quaternion pose :math:`\mathbf{p}_{q} = [\mathbf{x}_c, \mathbf{q}] = [x, y, z, q_i, q_j, q_k, q_r]`
    forward by one time-increment :math:`Δt`, given the velocity represented in quaternion form :math:`\mathbf{V}_q`.
    Where :math:`\mathbf{P}_q (t+1) = \mathbf{P}_q(t) × \mathbf{V}_q`, :math:`t` is in seconds, and :math:`×` denotes
    the hamilton product.\n
    `[reference] <https://en.wikipedia.org/wiki/Quaternion>`_

    Parameters
    ----------
    quat_pose
        Quaternion pose. *[batch_shape,7]*
    quat_vel
        Quaternion velocity. *[batch_shape,7]*
    delta_t
        Time step in seconds, for incrementing the quaternion pose by the velocity quaternion.

    Returns
    -------
    ret
        Incremented quaternion pose *[batch_shape,7]*

    """

    # BS x 4
    current_quaternion = quat_pose[..., 3:7]
    quaternion_vel = quat_vel[..., 3:7]
    quaternion_transform = ivy_quat.scale_quaternion_rotation_angle(
        quaternion_vel, delta_t
    )
    new_quaternion = ivy_quat.hamilton_product(current_quaternion, quaternion_transform)

    # BS x 7
    return ivy.concat(
        [quat_pose[..., 0:3] + quat_vel[..., 0:3] * delta_t, new_quaternion], axis=-1
    )
