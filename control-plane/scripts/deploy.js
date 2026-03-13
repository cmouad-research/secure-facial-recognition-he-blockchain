async function main() {
  const CP = await ethers.getContractFactory("ControlPlane");
  const cp = await CP.deploy();
  await cp.deployed();
  console.log(cp.address);
}
main().catch((e)=>{ console.error(e); process.exit(1); });
