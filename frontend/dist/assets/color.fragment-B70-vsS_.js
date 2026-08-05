import{S as n}from"./sindarius-gcodeviewer.es-ByZpGCWv.js";import"./clipPlaneFragment-GS6l6dhN.js";import"./fogFragment-BuTBaML-.js";import"./index-rN2NPx_y.js";import"./react-vendor-9t-2b6dQ.js";import"./icons-CNFEcl-l.js";const e="colorPixelShader",r=`#if defined(VERTEXCOLOR) || defined(INSTANCESCOLOR) && defined(INSTANCES)
#define VERTEXCOLOR
varying vColor: vec4f;
#else
uniform color: vec4f;
#endif
#include<clipPlaneFragmentDeclaration>
#include<fogFragmentDeclaration>
#define CUSTOM_FRAGMENT_DEFINITIONS
@fragment
fn main(input: FragmentInputs)->FragmentOutputs {
#define CUSTOM_FRAGMENT_MAIN_BEGIN
#include<clipPlaneFragment>
#if defined(VERTEXCOLOR) || defined(INSTANCESCOLOR) && defined(INSTANCES)
fragmentOutputs.color=input.vColor;
#else
fragmentOutputs.color=uniforms.color;
#endif
#include<fogFragment>(color,fragmentOutputs.color)
#define CUSTOM_FRAGMENT_MAIN_END
}`;n.ShadersStoreWGSL[e]||(n.ShadersStoreWGSL[e]=r);const l={name:e,shader:r};export{l as colorPixelShaderWGSL};
