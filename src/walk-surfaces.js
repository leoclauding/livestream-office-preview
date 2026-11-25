import * as THREE from "three";
import {Reflector} from "three/addons/objects/Reflector.js";
import {HDRLoader} from "three/addons/loaders/HDRLoader.js";

export async function loadSurfaceSet(library, root, renderer, mobile) {
  const loader=new THREE.TextureLoader();
  const anisotropy=Math.min(renderer.capabilities.getMaxAnisotropy(),mobile?4:8);
  const texture=async(name,channel)=>{
    const map=await loader.loadAsync(new URL(`materials/${name}-${channel}.jpg`,root).href);
    map.flipY=false;
    map.colorSpace=channel==="color"?THREE.SRGBColorSpace:THREE.NoColorSpace;
    map.wrapS=map.wrapT=THREE.RepeatWrapping;
    map.anisotropy=anisotropy;
    return map;
  };
  const byKey=new Map();
  const [sky]=await Promise.all([
    new HDRLoader().loadAsync(new URL("materials/rooftop.hdr",root).href),
    ...Object.entries(library).map(async([name,spec])=>{
      const [map,normalMap,roughnessMap]=await Promise.all(["color","normal","roughness"].map(channel=>texture(name,channel)));
      for(const key of spec.keys)byKey.set(key,{name,spec,map,normalMap,roughnessMap});
    })
  ]);
  sky.mapping=THREE.EquirectangularReflectionMapping;
  return {sky,byKey};
}

export function setSurface(material,maps) {
  const {name,spec,map,normalMap,roughnessMap}=maps;
  material.color.set(spec.tint);
  material.map=map;material.normalMap=normalMap;material.roughnessMap=roughnessMap;
  material.normalScale.setScalar(spec.normal);
  material.roughness=1;
  material.metalness=0;
  material.envMapIntensity=name==="stone"?.82:.63;
  if(material.isMeshPhysicalMaterial){
    material.clearcoat=spec.coat;
    material.clearcoatRoughness=.21;
  }
  const [low,high]=spec.roughness;
  material.onBeforeCompile=shader=>{
    shader.fragmentShader=shader.fragmentShader.replace("#include <roughnessmap_fragment>",`
      float roughnessFactor = roughness;
      #ifdef USE_ROUGHNESSMAP
      roughnessFactor = mix(${low.toFixed(3)}, ${high.toFixed(3)}, texture2D(roughnessMap, vRoughnessMapUv).g);
      #endif
    `);
  };
  material.customProgramCacheKey=()=>`scan-${name}-${low}-${high}`;
  material.needsUpdate=true;
}

export function makeCorridorReflection(mobile) {
  // Only this stone aisle has a planar pass. Fresnel and the soft sampling
  // keep reflection subordinate to the underlying detailed stone material.
  const width=mobile?320:608,height=mobile?384:704;
  const shader={
    name:"PolishedStoneCoat",
    uniforms:{color:{value:null},tDiffuse:{value:null},textureMatrix:{value:null},pixel:{value:new THREE.Vector2(1/width,1/height)}},
    vertexShader:`
      uniform mat4 textureMatrix;
      varying vec4 vProjection;
      varying vec3 vWorld;
      void main() {
        vProjection = textureMatrix * vec4(position, 1.0);
        vWorld = (modelMatrix * vec4(position, 1.0)).xyz;
        gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
      }
    `,
    fragmentShader:`
      uniform sampler2D tDiffuse;
      uniform vec2 pixel;
      varying vec4 vProjection;
      varying vec3 vWorld;
      void main() {
        vec2 uv = vProjection.xy/vProjection.w;
        vec2 stepUV = pixel*1.30;
        vec3 tone = texture2D(tDiffuse,uv).rgb * .42;
        tone += (texture2D(tDiffuse,uv+vec2(stepUV.x,0.)).rgb + texture2D(tDiffuse,uv-vec2(stepUV.x,0.)).rgb
               + texture2D(tDiffuse,uv+vec2(0.,stepUV.y)).rgb + texture2D(tDiffuse,uv-vec2(0.,stepUV.y)).rgb) * .145;
        float cosine = abs(normalize(cameraPosition-vWorld).y);
        float strength = .062 + .27*pow(1.-cosine, 3.0);
        gl_FragColor = vec4(tone,strength);
        #include <tonemapping_fragment>
        #include <colorspace_fragment>
      }
    `
  };
  const reflector=new Reflector(new THREE.PlaneGeometry(2.26,14.4),{
    shader,textureWidth:width,textureHeight:height,multisample:0,clipBias:.00029
  });
  reflector.rotation.x=-Math.PI/2;
  reflector.position.set(-5.442,.006,-6.91);
  reflector.material.transparent=true;
  reflector.material.depthWrite=false;
  reflector.renderOrder=2;
  return reflector;
}
