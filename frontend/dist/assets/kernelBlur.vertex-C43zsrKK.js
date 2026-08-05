import{S as e}from"./sindarius-gcodeviewer.es-B_xu1QnT.js";import"./kernelBlurVaryingDeclaration-CByVr0Sj.js";import"./index-BA7oqd8V.js";import"./react-vendor-9t-2b6dQ.js";import"./icons-CNFEcl-l.js";const r="kernelBlurVertex",o="vertexOutputs.sampleCoord{X}=vertexOutputs.sampleCenter+uniforms.delta*KERNEL_OFFSET{X};";e.IncludesShadersStoreWGSL[r]||(e.IncludesShadersStoreWGSL[r]=o);const t="kernelBlurVertexShader",n=`attribute position: vec2f;uniform delta: vec2f;varying sampleCenter: vec2f;
#include<kernelBlurVaryingDeclaration>[0..varyingCount]
#define CUSTOM_VERTEX_DEFINITIONS
@vertex
fn main(input : VertexInputs)->FragmentInputs {const madd: vec2f= vec2f(0.5,0.5);
#define CUSTOM_VERTEX_MAIN_BEGIN
vertexOutputs.sampleCenter=(input.position*madd+madd);
#include<kernelBlurVertex>[0..varyingCount]
vertexOutputs.position= vec4f(input.position,0.0,1.0);
#define CUSTOM_VERTEX_MAIN_END
}`;e.ShadersStoreWGSL[t]||(e.ShadersStoreWGSL[t]=n);const p={name:t,shader:n};export{p as kernelBlurVertexShaderWGSL};
