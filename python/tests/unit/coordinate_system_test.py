from ecostress.coordinate_system import (
    m_jem_to_a,
    m_ef_to_jem,
    m_10_to_ef,
    m_optics_to_10,
    m_camera_to_optics,
)


def test_coordinate_system():
    print(m_jem_to_a * m_ef_to_jem * m_10_to_ef * m_optics_to_10 * m_camera_to_optics)
