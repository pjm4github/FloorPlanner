import QtQuick
import QtQuick3D
import QtQuick3D.Helpers

Item {
    id: root

    View3D {
        id: view
        anchors.fill: parent

        // The active camera: a first-person camera bound to the plan camera's
        // live pose, or the orbit camera about the model centre. The MODE is
        // fixed when the window opens (cfg.firstPerson); the POSE moves live.
        camera: cfg.firstPerson ? fpCamera : orbitCamera

        environment: SceneEnvironment {
            clearColor: "#ffffff"
            backgroundMode: SceneEnvironment.Color
            antialiasingMode: SceneEnvironment.MSAA
            antialiasingQuality: SceneEnvironment.High
            // The whole reason to be here: two lines of ambient occlusion.
            aoEnabled: cfg.ao
            aoStrength: 75
            aoDistance: 30
            aoSoftness: 40
            tonemapMode: SceneEnvironment.TonemapModeLinear
        }

        Node {
            id: origin
            // a settable viewpoint (0252-report.md): the orbit's own two
            // angles and a zoom, each 0 / 1 for the home view -- what
            // `fp3dq.py --shot --yaw --pitch --zoom` sets, and what the
            // OrbitCameraController goes on changing by mouse
            eulerRotation.x: cfg.pitch
            eulerRotation.y: cfg.yaw
            PerspectiveCamera {
                id: orbitCamera
                z: cfg.distance * cfg.zoom
                y: cfg.distance * 0.45 * cfg.zoom
                clipNear: 1.0
                clipFar: cfg.distance * 20
                eulerRotation.x: -24
                fieldOfView: cfg.fov          // 60 for the view; a shot may narrow it
            }
        }

        // FIRST-PERSON camera: world-positioned (not on the orbit node), its
        // eye and aim bound to `pose`, which Python pushes live as the plan
        // camera moves (fp3dq.plan_to_qml_pose maps plan inches/aim -> QML).
        // A near plane close in, for standing inside a room.
        PerspectiveCamera {
            id: fpCamera
            position: Qt.vector3d(pose.eyeX, pose.eyeY, pose.eyeZ)
            eulerRotation: Qt.vector3d(pose.pitch, pose.yaw, 0)
            clipNear: 1.0
            clipFar: cfg.distance * 20
            fieldOfView: cfg.fov
        }

        DirectionalLight {                       // key, casts the shadows
            eulerRotation.x: -42
            eulerRotation.y: -35
            brightness: 1.15
            castsShadow: cfg.shadows
            shadowFactor: 65
            shadowMapQuality: Light.ShadowMapQualityHigh
            csmNumSplits: 2
        }
        DirectionalLight {                       // fill, no shadows
            eulerRotation.x: -12
            eulerRotation.y: 140
            brightness: 0.35
        }
        DirectionalLight {                       // sky bounce from below
            eulerRotation.x: 80
            brightness: 0.18
            color: "#d3e4b4"
        }

        Repeater3D {
            model: planMeshes
            Model {
                geometry: modelData.geom
                castsShadows: cfg.shadows
                receivesShadows: cfg.shadows
                opacity: modelData.alpha
                materials: PrincipledMaterial {
                    baseColor: modelData.color
                    vertexColorsEnabled: true
                    roughness: modelData.roughness
                    metalness: modelData.metalness
                    alphaMode: modelData.alpha < 1.0
                                 ? PrincipledMaterial.Blend
                                 : PrincipledMaterial.Opaque
                }
            }
        }
    }

    OrbitCameraController {
        anchors.fill: view
        origin: origin
        camera: orbitCamera
        enabled: !cfg.firstPerson          // the plan camera drives the first-person view
    }

    Text {
        anchors { left: parent.left; bottom: parent.bottom; margins: 6 }
        color: "#98a0ac"
        font.pixelSize: 12
        text: cfg.status
    }
}
