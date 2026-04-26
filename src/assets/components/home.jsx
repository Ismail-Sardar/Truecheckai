/*import Contents from "./contents";
import Feature from "./features";

function Home() {
  return (
    <>
      <div id="contents">
        <Contents />
      </div>
      <div id="features">
        <Feature />
      </div>
    </>
  );
}

export default Home;
*/

import Contents from "./contents";
import Feature from "./features";
import About from "./about";

function Home() {
  return (
    <>
      <Contents />
      <Feature />
      <About />
    </>
  );
}
export default Home;
