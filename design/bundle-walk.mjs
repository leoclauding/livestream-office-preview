import {createRequire} from "node:module";
import {fileURLToPath,pathToFileURL} from "node:url";
import {dirname,resolve} from "node:path";
const project = fileURLToPath(new URL("../",import.meta.url));
const fromProject = createRequire(new URL("../package.json",import.meta.url));
const shared = createRequire(new URL("../../apartment-walkthrough/package.json",import.meta.url));
let dependencies=fromProject;
try { dependencies.resolve("rolldown"); } catch { dependencies=shared; }
const {rolldown}=await import(pathToFileURL(dependencies.resolve("rolldown")).href);
const threeRoot=resolve(dirname(dependencies.resolve("three")),"..");
const bundle=await rolldown({
  input:resolve(project,"src/walk.js"),
  resolve:{alias:{
    "three/addons":resolve(threeRoot,"examples/jsm"),
    "three":resolve(threeRoot,"build/three.module.js")
  }}
});
await bundle.write({file:resolve(project,"assets/walk.js"),format:"esm",minify:true});
await bundle.close();
