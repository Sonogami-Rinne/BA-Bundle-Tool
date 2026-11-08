"""Preserve ShaderLab property references until a material is available."""

BLEND_FIELDS = {
    'srcBlend': 'srcBlend', 'dstBlend': 'destBlend',
    'srcBlendAlpha': 'srcBlendAlpha', 'dstBlendAlpha': 'destBlendAlpha',
    'blendOp': 'blendOp', 'blendOpAlpha': 'blendOpAlpha', 'colMask': 'colMask',
}


def extract_blend_info(rt):
    return {target: dict(rt[source]) for target, source in BLEND_FIELDS.items()}


def resolve_blend_info(blend_info, properties, material_properties):
    result = {}
    for field, state in blend_info.items():
        # Accept literal values from older recorder files as well.
        if not isinstance(state, dict):
            result[field] = state
            continue
        name = state.get('name')
        if not name or name == '<noninit>':
            result[field] = state['val']
            continue
        if name in material_properties:
            value = material_properties[name]
        elif name in properties:
            value = properties[name]['value']
        else:
            raise ValueError(f'Render state {field} references missing property {name}')
        # Shader defaults use single-element arrays; material floats are scalars.
        if isinstance(value, (list, tuple)) and len(value) == 1:
            value = value[0]
        if not isinstance(value, (int, float)):
            raise ValueError(f'Render state {field} property {name} must be numeric: {value!r}')
        result[field] = value
    return result
