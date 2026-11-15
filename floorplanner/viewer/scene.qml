import QtQuick
import QtQuick3D
import QtQuick3D.Helpers

Item {
    id: root
    focus: true

    // 0328 (3D-camera PHASE 2): the view becomes a CONTROLLER. The machinery
    // below is inert unless this is a first-person view that can walk
    // (cfg.walk) and the user has CAPTURED it (walkBridge.captured) by clicking
    // the view; Esc releases. Input is Option B: QML hands Python the key/mouse
    // DELTAS (walkBridge.step), Python integrates them and moves the plan
    // camera, and fpCamera stays bound to `pose` (which the write-back re-feeds).
    // Moving only in the plane keeps the eye at 65in by construction (C1).
    property bool walking: cfg.walk && walkBridge.captured
    property real stepIn: 3.0              // plan inches per tick, walking
    property real runIn: 8.0               // Shift = run
    property real yawStep: 2.5             // degrees per tick, Q/E turn
    property real lookSens: 0.15           // degrees per pixel, mouse-look
    property bool keyW: false
    property bool keyA: false
    property bool keyS: false
    property bool keyD: false
    property bool keyQ: false
    property bool keyE: false
    property bool keyShift: false

    onWalkingChanged: if (!walking) {       // drop every held key on release
        keyW = false; keyA = false; keyS = false; keyD = false;
        keyQ = false; keyE = false; keyShift = false;
    }

    Keys.onPressed: (event) => {
        if (event.key === Qt.Key_Escape && walkBridge.captured) {
            walkBridge.release(); event.accepted = true; return;
        }
        if (!root.walking) return;
        switch (event.key) {
        case Qt.Key_W: root.keyW = true; event.accepted = true; break;
        case Qt.Key_A: root.keyA = true; event.accepted = true; break;
        case Qt.Key_S: root.keyS = true; event.accepted = true; break;
        case Qt.Key_D: root.keyD = true; event.accepted = true; break;
        case Qt.Key_Q: root.keyQ = true; event.accepted = true; break;
        case Qt.Key_E: root.keyE = true; event.accepted = true; break;
        case Qt.Key_Shift: root.keyShift = true; event.accepted = true; break;
        }
    }
    Keys.onReleased: (event) => {
        switch (event.key) {
        case Qt.Key_W: root.keyW = false; event.accepted = true; break;
        case Qt.Key_A: root.keyA = false; event.accepted = true; break;
        case Qt.Key_S: root.keyS = false; event.accepted = true; break;
        case Qt.Key_D: root.keyD = false; event.accepted = true; break;
        case Qt.Key_Q: root.keyQ = false; event.accepted = true; break;
        case Qt.Key_E: root.keyE = false; event.accepted = true; break;
        case Qt.Key_Shift: root.keyShift = false; event.accepted = true; break;
        }
    }

    // One bridge.step per tick while captured: WASD translate (camera-relative,
    // horizontal), Q/E yaw, Shift = run. The deltas integrate in Python.
    Timer {
        interval: 16; repeat: true; running: root.walking
        onTriggered: {
            var s = root.keyShift ? root.runIn : root.stepIn;
            var fwd = (root.keyW ? s : 0) - (root.keyS ? s : 0);
            var strafe = (root.keyD ? s : 0) - (root.keyA ? s : 0);
            var dyaw = (root.keyE ? root.yawStep : 0) - (root.keyQ ? root.yawStep : 0);
            if (fwd !== 0 || strafe !== 0 || dyaw !== 0)
                walkBridge.step(fwd, strafe, dyaw, 0);
        }
    }

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

        // The plan's own light fixtures (0333 §3). One node per entry in the
        // lists Python fills from `model.lights`; both lists are empty when the
        // plan has no lights, so the scene is then exactly the three
        // directional lights above. NONE of these cast shadows to start with
        // (0333 §3.2): a shadow-casting point light needs a six-face cube map
        // every frame, the expensive part -- held off until Patrick has walked
        // a lit plan and can say it is worth the cost.
        Repeater3D {
            model: planPointLights
            PointLight {
                position: modelData.position
                color: modelData.color
                brightness: modelData.brightness
                castsShadow: false
            }
        }
        Repeater3D {
            model: planSpotLights
            SpotLight {
                position: modelData.position
                eulerRotation.x: -90          // aim straight DOWN (0333 §3)
                color: modelData.color
                brightness: modelData.brightness
                coneAngle: modelData.coneDeg
                innerConeAngle: modelData.coneDeg * 0.7
                castsShadow: false
            }
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
                    // A light's lens glows its own colour so it reads as lit
                    // whatever the scene lighting does (0333 §3.4); every other
                    // mesh carries (0,0,0) here and is unaffected.
                    emissiveFactor: modelData.emissive
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

    // 0328 (Phase 2): click to CAPTURE the walk (grab/hide the cursor, mouse-look
    // live); Esc releases (Keys.onPressed above). Enabled only on a walkable
    // first-person view, so the orbit view's own controller is untouched. While
    // captured, pointer motion is a mouse-look delta: yaw (writes back to the
    // plan camera) and view-local pitch.
    MouseArea {
        id: walkMouse
        anchors.fill: parent
        enabled: cfg.walk
        hoverEnabled: root.walking
        acceptedButtons: Qt.LeftButton
        cursorShape: root.walking ? Qt.BlankCursor : Qt.ArrowCursor
        property real lastX: 0
        property real lastY: 0
        property bool have: false
        onClicked: (mouse) => {
            if (!walkBridge.captured) {
                have = false;
                root.forceActiveFocus();       // WASD needs the keyboard focus
                walkBridge.capture();
            }
        }
        onPositionChanged: (mouse) => {
            if (!root.walking) { have = false; return; }
            if (have) {
                var dx = mouse.x - lastX;
                var dy = mouse.y - lastY;
                if (dx !== 0 || dy !== 0)      // dx -> yaw, dy -> view-local pitch
                    walkBridge.step(0, 0, dx * root.lookSens, -dy * root.lookSens);
            }
            lastX = mouse.x; lastY = mouse.y; have = true;
        }
    }

    Text {
        anchors { left: parent.left; bottom: parent.bottom; margins: 6 }
        color: "#98a0ac"
        font.pixelSize: 12
        text: cfg.status
    }

    // the walk hint: how to capture / release, only on a walkable view
    Text {
        visible: cfg.walk
        anchors { right: parent.right; bottom: parent.bottom; margins: 6 }
        color: "#98a0ac"
        font.pixelSize: 12
        text: root.walking ? "WASD move · Q/E turn · Shift run · mouse look · Esc release"
                           : "click to walk"
    }
}
