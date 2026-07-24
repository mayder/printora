import{S as r}from"./sindarius-gcodeviewer.es-DG2Py5_f.js";import"./clipPlaneFragment-7-iY-y1L.js";import"./logDepthDeclaration-B1jtbPkS.js";import"./logDepthFragment-DY-Q6dAK.js";import"./index-CprTTvVc.js";import"./react-vendor-9t-2b6dQ.js";import"./icons-BQGxjbGj.js";const e="linePixelShader",t=`#include<clipPlaneFragmentDeclaration>
uniform color: vec4f;
#include<logDepthDeclaration>
#define CUSTOM_FRAGMENT_DEFINITIONS
@fragment
fn main(input: FragmentInputs)->FragmentOutputs {
#define CUSTOM_FRAGMENT_MAIN_BEGIN
#include<logDepthFragment>
#include<clipPlaneFragment>
fragmentOutputs.color=uniforms.color;
#define CUSTOM_FRAGMENT_MAIN_END
}`;r.ShadersStoreWGSL[e]||(r.ShadersStoreWGSL[e]=t);const S={name:e,shader:t};export{S as linePixelShaderWGSL};
