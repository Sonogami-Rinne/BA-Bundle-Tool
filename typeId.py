"""
copy from unitypy
"""


class ClassIDType:
    UnknownType = -1
    Object = 0
    GameObject = 1
    Component = 2
    LevelGameManager = 3
    Transform = 4
    TimeManager = 5
    GlobalGameManager = 6
    Behaviour = 8
    GameManager = 9
    AudioManager = 11
    ParticleAnimator = 12
    InputManager = 13
    EllipsoidParticleEmitter = 15
    Pipeline = 17
    EditorExtension = 18
    Physics2DSettings = 19
    Camera = 20
    Material = 21
    MeshRenderer = 23
    Renderer = 25
    ParticleRenderer = 26
    Texture = 27
    Texture2D = 28
    OcclusionCullingSettings = 29
    GraphicsSettings = 30
    MeshFilter = 33
    OcclusionPortal = 41
    Mesh = 43
    Skybox = 45
    QualitySettings = 47
    Shader = 48
    TextAsset = 49
    Rigidbody2D = 50
    Physics2DManager = 51
    Collider2D = 53
    Rigidbody = 54
    PhysicsManager = 55
    Collider = 56
    Joint = 57
    CircleCollider2D = 58
    HingeJoint = 59
    PolygonCollider2D = 60
    BoxCollider2D = 61
    PhysicsMaterial2D = 62
    MeshCollider = 64
    BoxCollider = 65
    CompositeCollider2D = 66
    EdgeCollider2D = 68
    CapsuleCollider2D = 70
    ComputeShader = 72
    AnimationClip = 74
    ConstantForce = 75
    WorldParticleCollider = 76
    TagManager = 78
    AudioListener = 81
    AudioSource = 82
    AudioClip = 83
    RenderTexture = 84
    CustomRenderTexture = 86
    MeshParticleEmitter = 87
    ParticleEmitter = 88
    Cubemap = 89
    Avatar = 90
    AnimatorController = 91
    GUILayer = 92
    RuntimeAnimatorController = 93
    ScriptMapper = 94
    Animator = 95
    TrailRenderer = 96
    DelayedCallManager = 98
    TextMesh = 102
    RenderSettings = 104
    Light = 108
    CGProgram = 109
    BaseAnimationTrack = 110
    Animation = 111
    MonoBehaviour = 114
    MonoScript = 115
    MonoManager = 116
    Texture3D = 117
    NewAnimationTrack = 118
    Projector = 119
    LineRenderer = 120
    Flare = 121
    Halo = 122
    LensFlare = 123
    FlareLayer = 124
    HaloLayer = 125
    NavMeshProjectSettings = 126
    HaloManager = 127
    Font = 128
    PlayerSettings = 129
    NamedObject = 130
    GUITexture = 131
    GUIText = 132
    GUIElement = 133
    PhysicMaterial = 134
    SphereCollider = 135
    CapsuleCollider = 136
    SkinnedMeshRenderer = 137
    FixedJoint = 138
    RaycastCollider = 140
    BuildSettings = 141
    AssetBundle = 142
    CharacterController = 143
    CharacterJoint = 144
    SpringJoint = 145
    WheelCollider = 146
    ResourceManager = 147
    NetworkView = 148
    NetworkManager = 149
    PreloadData = 150
    MovieTexture = 152
    ConfigurableJoint = 153
    TerrainCollider = 154
    MasterServerInterface = 155
    TerrainData = 156
    LightmapSettings = 157
    WebCamTexture = 158
    EditorSettings = 159
    InteractiveCloth = 160
    ClothRenderer = 161
    EditorUserSettings = 162
    SkinnedCloth = 163
    AudioReverbFilter = 164
    AudioHighPassFilter = 165
    AudioChorusFilter = 166
    AudioReverbZone = 167
    AudioEchoFilter = 168
    AudioLowPassFilter = 169
    AudioDistortionFilter = 170
    SparseTexture = 171
    AudioBehaviour = 180
    AudioFilter = 181
    WindZone = 182
    Cloth = 183
    SubstanceArchive = 184
    ProceduralMaterial = 185
    ProceduralTexture = 186
    Texture2DArray = 187
    CubemapArray = 188
    OffMeshLink = 191
    OcclusionArea = 192
    Tree = 193
    NavMeshObsolete = 194
    NavMeshAgent = 195
    NavMeshSettings = 196
    LightProbesLegacy = 197
    ParticleSystem = 198
    ParticleSystemRenderer = 199
    ShaderVariantCollection = 200
    LODGroup = 205
    BlendTree = 206
    Motion = 207
    NavMeshObstacle = 208
    SortingGroup = 210
    SpriteRenderer = 212
    Sprite = 213
    CachedSpriteAtlas = 214
    ReflectionProbe = 215
    ReflectionProbes = 216
    Terrain = 218
    LightProbeGroup = 220
    AnimatorOverrideController = 221
    CanvasRenderer = 222
    Canvas = 223
    RectTransform = 224
    CanvasGroup = 225
    BillboardAsset = 226
    BillboardRenderer = 227
    SpeedTreeWindAsset = 228
    AnchoredJoint2D = 229
    Joint2D = 230
    SpringJoint2D = 231
    DistanceJoint2D = 232
    HingeJoint2D = 233
    SliderJoint2D = 234
    WheelJoint2D = 235
    ClusterInputManager = 236
    BaseVideoTexture = 237
    NavMeshData = 238
    AudioMixer = 240
    AudioMixerController = 241
    AudioMixerGroupController = 243
    AudioMixerEffectController = 244
    AudioMixerSnapshotController = 245
    PhysicsUpdateBehaviour2D = 246
    ConstantForce2D = 247
    Effector2D = 248
    AreaEffector2D = 249
    PointEffector2D = 250
    PlatformEffector2D = 251
    SurfaceEffector2D = 252
    BuoyancyEffector2D = 253
    RelativeJoint2D = 254
    FixedJoint2D = 255
    FrictionJoint2D = 256
    TargetJoint2D = 257
    LightProbes = 258
    LightProbeProxyVolume = 259
    SampleClip = 271
    AudioMixerSnapshot = 272
    AudioMixerGroup = 273
    NScreenBridge = 280
    AssetBundleManifest = 290
    UnityAdsManager = 292
    RuntimeInitializeOnLoadManager = 300
    CloudWebServicesManager = 301
    UnityAnalyticsManager = 303
    CrashReportManager = 304
    PerformanceReportingManager = 305
    UnityConnectSettings = 310
    AvatarMask = 319
    PlayableDirector = 320
    VideoPlayer = 328
    VideoClip = 329
    ParticleSystemForceField = 330
    SpriteMask = 331
    WorldAnchor = 362
    OcclusionCullingData = 363
    SmallestEditorClassID = 1000
    PrefabInstance = 1001
    EditorExtensionImpl = 1002
    AssetImporter = 1003
    AssetDatabaseV1 = 1004
    Mesh3DSImporter = 1005
    TextureImporter = 1006
    ShaderImporter = 1007
    ComputeShaderImporter = 1008
    AudioImporter = 1020
    HierarchyState = 1026
    GUIDSerializer = 1027
    AssetMetaData = 1028
    DefaultAsset = 1029
    DefaultImporter = 1030
    TextScriptImporter = 1031
    SceneAsset = 1032
    NativeFormatImporter = 1034
    MonoImporter = 1035
    AssetServerCache = 1037
    LibraryAssetImporter = 1038
    ModelImporter = 1040
    FBXImporter = 1041
    TrueTypeFontImporter = 1042
    MovieImporter = 1044
    EditorBuildSettings = 1045
    DDSImporter = 1046
    InspectorExpandedState = 1048
    AnnotationManager = 1049
    PluginImporter = 1050
    EditorUserBuildSettings = 1051
    PVRImporter = 1052
    ASTCImporter = 1053
    KTXImporter = 1054
    IHVImageFormatImporter = 1055
    AnimatorStateTransition = 1101
    AnimatorState = 1102
    HumanTemplate = 1105
    AnimatorStateMachine = 1107
    PreviewAnimationClip = 1108
    AnimatorTransition = 1109
    SpeedTreeImporter = 1110
    AnimatorTransitionBase = 1111
    SubstanceImporter = 1112
    LightmapParameters = 1113
    LightingDataAsset = 1120
    GISRaster = 1121
    GISRasterImporter = 1122
    CadImporter = 1123
    SketchUpImporter = 1124
    BuildReport = 1125
    PackedAssets = 1126
    VideoClipImporter = 1127
    ActivationLogComponent = 2000
    int = 100000
    bool = 100001
    float = 100002
    MonoObject = 100003
    Collision = 100004
    Vector3f = 100005
    RootMotionData = 100006
    Collision2D = 100007
    AudioMixerLiveUpdateFloat = 100008
    AudioMixerLiveUpdateBool = 100009
    Polygon2D = 100010
    void = 100011
    TilemapCollider2D = 19719996
    AssetImporterLog = 41386430
    VFXRenderer = 73398921
    SerializableManagedRefTestClass = 76251197
    Grid = 156049354
    ScenesUsingAssets = 156483287
    ArticulationBody = 171741748
    Preset = 181963792
    EmptyObject = 277625683
    IConstraint = 285090594
    TestObjectWithSpecialLayoutOne = 293259124
    AssemblyDefinitionReferenceImporter = 294290339
    SiblingDerived = 334799969
    TestObjectWithSerializedMapStringNonAlignedStruct = 342846651
    SubDerived = 367388927
    AssetImportInProgressProxy = 369655926
    PluginBuildInfo = 382020655
    EditorProjectAccess = 426301858
    PrefabImporter = 468431735
    TestObjectWithSerializedArray = 478637458
    TestObjectWithSerializedAnimationCurve = 478637459
    TilemapRenderer = 483693784
    ScriptableCamera = 488575907
    SpriteAtlasAsset = 612988286
    SpriteAtlasDatabase = 638013454
    AudioBuildInfo = 641289076
    CachedSpriteAtlasRuntimeData = 644342135
    RendererFake = 646504946
    AssemblyDefinitionReferenceAsset = 662584278
    BuiltAssetBundleInfoSet = 668709126
    SpriteAtlas = 687078895
    RayTracingShaderImporter = 747330370
    RayTracingShader = 825902497
    LightingSettings = 850595691
    PlatformModuleSetup = 877146078
    VersionControlSettings = 890905787
    AimConstraint = 895512359
    VFXManager = 937362698
    VisualEffectSubgraph = 994735392
    VisualEffectSubgraphOperator = 994735403
    VisualEffectSubgraphBlock = 994735404
    LocalizationImporter = 1027052791
    Derived = 1091556383
    PropertyModificationsTargetTestObject = 1111377672
    ReferencesArtifactGenerator = 1114811875
    AssemblyDefinitionAsset = 1152215463
    SceneVisibilityState = 1154873562
    LookAtConstraint = 1183024399
    SpriteAtlasImporter = 1210832254
    MultiArtifactTestImporter = 1223240404
    GameObjectRecorder = 1268269756
    LightingDataAssetParent = 1325145578
    PresetManager = 1386491679
    TestObjectWithSpecialLayoutTwo = 1392443030
    StreamingManager = 1403656975
    LowerResBlitTexture = 1480428607
    StreamingController = 1542919678
    RenderPassAttachment = 1571458007
    TestObjectVectorPairStringBool = 1628831178
    GridLayout = 1742807556
    AssemblyDefinitionImporter = 1766753193
    ParentConstraint = 1773428102
    FakeComponent = 1803986026
    PositionConstraint = 1818360608
    RotationConstraint = 1818360609
    ScaleConstraint = 1818360610
    Tilemap = 1839735485
    PackageManifest = 1896753125
    PackageManifestImporter = 1896753126
    TerrainLayer = 1953259897
    SpriteShapeRenderer = 1971053207
    NativeObjectType = 1977754360
    TestObjectWithSerializedMapStringBool = 1981279845
    SerializableManagedHost = 1995898324
    VisualEffectAsset = 2058629509
    VisualEffectImporter = 2058629510
    VisualEffectResource = 2058629511
    VisualEffectObject = 2059678085
    VisualEffect = 2083052967
    LocalizationAsset = 2083778819
    ScriptedImporter = 2089858483


inverse_map = {
    "-1": "UnknownType",
    "0": "Object",
    "1": "GameObject",
    "2": "Component",
    "3": "LevelGameManager",
    "4": "Transform",
    "5": "TimeManager",
    "6": "GlobalGameManager",
    "8": "Behaviour",
    "9": "GameManager",
    "11": "AudioManager",
    "12": "ParticleAnimator",
    "13": "InputManager",
    "15": "EllipsoidParticleEmitter",
    "17": "Pipeline",
    "18": "EditorExtension",
    "19": "Physics2DSettings",
    "20": "Camera",
    "21": "Material",
    "23": "MeshRenderer",
    "25": "Renderer",
    "26": "ParticleRenderer",
    "27": "Texture",
    "28": "Texture2D",
    "29": "OcclusionCullingSettings",
    "30": "GraphicsSettings",
    "33": "MeshFilter",
    "41": "OcclusionPortal",
    "43": "Mesh",
    "45": "Skybox",
    "47": "QualitySettings",
    "48": "Shader",
    "49": "TextAsset",
    "50": "Rigidbody2D",
    "51": "Physics2DManager",
    "53": "Collider2D",
    "54": "Rigidbody",
    "55": "PhysicsManager",
    "56": "Collider",
    "57": "Joint",
    "58": "CircleCollider2D",
    "59": "HingeJoint",
    "60": "PolygonCollider2D",
    "61": "BoxCollider2D",
    "62": "PhysicsMaterial2D",
    "64": "MeshCollider",
    "65": "BoxCollider",
    "66": "CompositeCollider2D",
    "68": "EdgeCollider2D",
    "70": "CapsuleCollider2D",
    "72": "ComputeShader",
    "74": "AnimationClip",
    "75": "ConstantForce",
    "76": "WorldParticleCollider",
    "78": "TagManager",
    "81": "AudioListener",
    "82": "AudioSource",
    "83": "AudioClip",
    "84": "RenderTexture",
    "86": "CustomRenderTexture",
    "87": "MeshParticleEmitter",
    "88": "ParticleEmitter",
    "89": "Cubemap",
    "90": "Avatar",
    "91": "AnimatorController",
    "92": "GUILayer",
    "93": "RuntimeAnimatorController",
    "94": "ScriptMapper",
    "95": "Animator",
    "96": "TrailRenderer",
    "98": "DelayedCallManager",
    "102": "TextMesh",
    "104": "RenderSettings",
    "108": "Light",
    "109": "CGProgram",
    "110": "BaseAnimationTrack",
    "111": "Animation",
    "114": "MonoBehaviour",
    "115": "MonoScript",
    "116": "MonoManager",
    "117": "Texture3D",
    "118": "NewAnimationTrack",
    "119": "Projector",
    "120": "LineRenderer",
    "121": "Flare",
    "122": "Halo",
    "123": "LensFlare",
    "124": "FlareLayer",
    "125": "HaloLayer",
    "126": "NavMeshProjectSettings",
    "127": "HaloManager",
    "128": "Font",
    "129": "PlayerSettings",
    "130": "NamedObject",
    "131": "GUITexture",
    "132": "GUIText",
    "133": "GUIElement",
    "134": "PhysicMaterial",
    "135": "SphereCollider",
    "136": "CapsuleCollider",
    "137": "SkinnedMeshRenderer",
    "138": "FixedJoint",
    "140": "RaycastCollider",
    "141": "BuildSettings",
    "142": "AssetBundle",
    "143": "CharacterController",
    "144": "CharacterJoint",
    "145": "SpringJoint",
    "146": "WheelCollider",
    "147": "ResourceManager",
    "148": "NetworkView",
    "149": "NetworkManager",
    "150": "PreloadData",
    "152": "MovieTexture",
    "153": "ConfigurableJoint",
    "154": "TerrainCollider",
    "155": "MasterServerInterface",
    "156": "TerrainData",
    "157": "LightmapSettings",
    "158": "WebCamTexture",
    "159": "EditorSettings",
    "160": "InteractiveCloth",
    "161": "ClothRenderer",
    "162": "EditorUserSettings",
    "163": "SkinnedCloth",
    "164": "AudioReverbFilter",
    "165": "AudioHighPassFilter",
    "166": "AudioChorusFilter",
    "167": "AudioReverbZone",
    "168": "AudioEchoFilter",
    "169": "AudioLowPassFilter",
    "170": "AudioDistortionFilter",
    "171": "SparseTexture",
    "180": "AudioBehaviour",
    "181": "AudioFilter",
    "182": "WindZone",
    "183": "Cloth",
    "184": "SubstanceArchive",
    "185": "ProceduralMaterial",
    "186": "ProceduralTexture",
    "187": "Texture2DArray",
    "188": "CubemapArray",
    "191": "OffMeshLink",
    "192": "OcclusionArea",
    "193": "Tree",
    "194": "NavMeshObsolete",
    "195": "NavMeshAgent",
    "196": "NavMeshSettings",
    "197": "LightProbesLegacy",
    "198": "ParticleSystem",
    "199": "ParticleSystemRenderer",
    "200": "ShaderVariantCollection",
    "205": "LODGroup",
    "206": "BlendTree",
    "207": "Motion",
    "208": "NavMeshObstacle",
    "210": "SortingGroup",
    "212": "SpriteRenderer",
    "213": "Sprite",
    "214": "CachedSpriteAtlas",
    "215": "ReflectionProbe",
    "216": "ReflectionProbes",
    "218": "Terrain",
    "220": "LightProbeGroup",
    "221": "AnimatorOverrideController",
    "222": "CanvasRenderer",
    "223": "Canvas",
    "224": "RectTransform",
    "225": "CanvasGroup",
    "226": "BillboardAsset",
    "227": "BillboardRenderer",
    "228": "SpeedTreeWindAsset",
    "229": "AnchoredJoint2D",
    "230": "Joint2D",
    "231": "SpringJoint2D",
    "232": "DistanceJoint2D",
    "233": "HingeJoint2D",
    "234": "SliderJoint2D",
    "235": "WheelJoint2D",
    "236": "ClusterInputManager",
    "237": "BaseVideoTexture",
    "238": "NavMeshData",
    "240": "AudioMixer",
    "241": "AudioMixerController",
    "243": "AudioMixerGroupController",
    "244": "AudioMixerEffectController",
    "245": "AudioMixerSnapshotController",
    "246": "PhysicsUpdateBehaviour2D",
    "247": "ConstantForce2D",
    "248": "Effector2D",
    "249": "AreaEffector2D",
    "250": "PointEffector2D",
    "251": "PlatformEffector2D",
    "252": "SurfaceEffector2D",
    "253": "BuoyancyEffector2D",
    "254": "RelativeJoint2D",
    "255": "FixedJoint2D",
    "256": "FrictionJoint2D",
    "257": "TargetJoint2D",
    "258": "LightProbes",
    "259": "LightProbeProxyVolume",
    "271": "SampleClip",
    "272": "AudioMixerSnapshot",
    "273": "AudioMixerGroup",
    "280": "NScreenBridge",
    "290": "AssetBundleManifest",
    "292": "UnityAdsManager",
    "300": "RuntimeInitializeOnLoadManager",
    "301": "CloudWebServicesManager",
    "303": "UnityAnalyticsManager",
    "304": "CrashReportManager",
    "305": "PerformanceReportingManager",
    "310": "UnityConnectSettings",
    "319": "AvatarMask",
    "320": "PlayableDirector",
    "328": "VideoPlayer",
    "329": "VideoClip",
    "330": "ParticleSystemForceField",
    "331": "SpriteMask",
    "362": "WorldAnchor",
    "363": "OcclusionCullingData",
    "1000": "SmallestEditorClassID",
    "1001": "PrefabInstance",
    "1002": "EditorExtensionImpl",
    "1003": "AssetImporter",
    "1004": "AssetDatabaseV1",
    "1005": "Mesh3DSImporter",
    "1006": "TextureImporter",
    "1007": "ShaderImporter",
    "1008": "ComputeShaderImporter",
    "1020": "AudioImporter",
    "1026": "HierarchyState",
    "1027": "GUIDSerializer",
    "1028": "AssetMetaData",
    "1029": "DefaultAsset",
    "1030": "DefaultImporter",
    "1031": "TextScriptImporter",
    "1032": "SceneAsset",
    "1034": "NativeFormatImporter",
    "1035": "MonoImporter",
    "1037": "AssetServerCache",
    "1038": "LibraryAssetImporter",
    "1040": "ModelImporter",
    "1041": "FBXImporter",
    "1042": "TrueTypeFontImporter",
    "1044": "MovieImporter",
    "1045": "EditorBuildSettings",
    "1046": "DDSImporter",
    "1048": "InspectorExpandedState",
    "1049": "AnnotationManager",
    "1050": "PluginImporter",
    "1051": "EditorUserBuildSettings",
    "1052": "PVRImporter",
    "1053": "ASTCImporter",
    "1054": "KTXImporter",
    "1055": "IHVImageFormatImporter",
    "1101": "AnimatorStateTransition",
    "1102": "AnimatorState",
    "1105": "HumanTemplate",
    "1107": "AnimatorStateMachine",
    "1108": "PreviewAnimationClip",
    "1109": "AnimatorTransition",
    "1110": "SpeedTreeImporter",
    "1111": "AnimatorTransitionBase",
    "1112": "SubstanceImporter",
    "1113": "LightmapParameters",
    "1120": "LightingDataAsset",
    "1121": "GISRaster",
    "1122": "GISRasterImporter",
    "1123": "CadImporter",
    "1124": "SketchUpImporter",
    "1125": "BuildReport",
    "1126": "PackedAssets",
    "1127": "VideoClipImporter",
    "2000": "ActivationLogComponent",
    "100000": "int",
    "100001": "bool",
    "100002": "float",
    "100003": "MonoObject",
    "100004": "Collision",
    "100005": "Vector3f",
    "100006": "RootMotionData",
    "100007": "Collision2D",
    "100008": "AudioMixerLiveUpdateFloat",
    "100009": "AudioMixerLiveUpdateBool",
    "100010": "Polygon2D",
    "100011": "void",
    "19719996": "TilemapCollider2D",
    "41386430": "AssetImporterLog",
    "73398921": "VFXRenderer",
    "76251197": "SerializableManagedRefTestClass",
    "156049354": "Grid",
    "156483287": "ScenesUsingAssets",
    "171741748": "ArticulationBody",
    "181963792": "Preset",
    "277625683": "EmptyObject",
    "285090594": "IConstraint",
    "293259124": "TestObjectWithSpecialLayoutOne",
    "294290339": "AssemblyDefinitionReferenceImporter",
    "334799969": "SiblingDerived",
    "342846651": "TestObjectWithSerializedMapStringNonAlignedStruct",
    "367388927": "SubDerived",
    "369655926": "AssetImportInProgressProxy",
    "382020655": "PluginBuildInfo",
    "426301858": "EditorProjectAccess",
    "468431735": "PrefabImporter",
    "478637458": "TestObjectWithSerializedArray",
    "478637459": "TestObjectWithSerializedAnimationCurve",
    "483693784": "TilemapRenderer",
    "488575907": "ScriptableCamera",
    "612988286": "SpriteAtlasAsset",
    "638013454": "SpriteAtlasDatabase",
    "641289076": "AudioBuildInfo",
    "644342135": "CachedSpriteAtlasRuntimeData",
    "646504946": "RendererFake",
    "662584278": "AssemblyDefinitionReferenceAsset",
    "668709126": "BuiltAssetBundleInfoSet",
    "687078895": "SpriteAtlas",
    "747330370": "RayTracingShaderImporter",
    "825902497": "RayTracingShader",
    "850595691": "LightingSettings",
    "877146078": "PlatformModuleSetup",
    "890905787": "VersionControlSettings",
    "895512359": "AimConstraint",
    "937362698": "VFXManager",
    "994735392": "VisualEffectSubgraph",
    "994735403": "VisualEffectSubgraphOperator",
    "994735404": "VisualEffectSubgraphBlock",
    "1027052791": "LocalizationImporter",
    "1091556383": "Derived",
    "1111377672": "PropertyModificationsTargetTestObject",
    "1114811875": "ReferencesArtifactGenerator",
    "1152215463": "AssemblyDefinitionAsset",
    "1154873562": "SceneVisibilityState",
    "1183024399": "LookAtConstraint",
    "1210832254": "SpriteAtlasImporter",
    "1223240404": "MultiArtifactTestImporter",
    "1268269756": "GameObjectRecorder",
    "1325145578": "LightingDataAssetParent",
    "1386491679": "PresetManager",
    "1392443030": "TestObjectWithSpecialLayoutTwo",
    "1403656975": "StreamingManager",
    "1480428607": "LowerResBlitTexture",
    "1542919678": "StreamingController",
    "1571458007": "RenderPassAttachment",
    "1628831178": "TestObjectVectorPairStringBool",
    "1742807556": "GridLayout",
    "1766753193": "AssemblyDefinitionImporter",
    "1773428102": "ParentConstraint",
    "1803986026": "FakeComponent",
    "1818360608": "PositionConstraint",
    "1818360609": "RotationConstraint",
    "1818360610": "ScaleConstraint",
    "1839735485": "Tilemap",
    "1896753125": "PackageManifest",
    "1896753126": "PackageManifestImporter",
    "1953259897": "TerrainLayer",
    "1971053207": "SpriteShapeRenderer",
    "1977754360": "NativeObjectType",
    "1981279845": "TestObjectWithSerializedMapStringBool",
    "1995898324": "SerializableManagedHost",
    "2058629509": "VisualEffectAsset",
    "2058629510": "VisualEffectImporter",
    "2058629511": "VisualEffectResource",
    "2059678085": "VisualEffectObject",
    "2083052967": "VisualEffect",
    "2083778819": "LocalizationAsset",
    "2089858483": "ScriptedImporter"
}
