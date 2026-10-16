<template>
  <div class="s-mars-scene" aria-hidden="true">
    <svg class="s-scene-cubes" viewBox="0 0 400 320" fill="none" preserveAspectRatio="none">
      <defs><linearGradient id="scene-cube-a" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#b3ceff" stop-opacity=".65"/><stop offset="1" stop-color="#dff5ff" stop-opacity=".2"/></linearGradient><linearGradient id="scene-cube-b"><stop stop-color="#85b3ff" stop-opacity=".45"/><stop offset="1" stop-color="#d2e9ff" stop-opacity=".15"/></linearGradient></defs>
      <path d="m10 75 115-45 165 64-115 45Z" fill="#e2f3ff" opacity=".5"/>
      <path d="m30 145 83-29 80 30-82 33Z" fill="url(#scene-cube-a)"/><path d="m30 145 81 34v89l-81-37Z" fill="url(#scene-cube-b)"/><path d="m111 179 82-33v87l-82 35Z" fill="#c8eaff" opacity=".6"/>
      <path d="m85 245 138-46 123 57-145 51Z" fill="#b8d9ff" opacity=".18"/>
      <path d="m154 82 13-6 15 6-14 7Z" fill="#c3eaff"/><path d="m154 82 14 7v20l-14-6Z" fill="#9eccff" opacity=".7"/><path d="m168 89 14-7v20l-14 7Z" fill="#b7e0ff" opacity=".8"/>
      <path d="m-20 45 100-42 151 57" stroke="white" stroke-opacity=".5" stroke-width="2"/>
    </svg>
    <div class="s-scene-planet"><div class="s-planet-ring"></div><div class="s-planet-ball"></div><div class="s-planet-ring s-ring-front"></div></div>
    <svg class="s-scene-platform" viewBox="0 0 370 190" fill="none"><path d="m3 132 235-90 130 45-231 100Z" fill="#a8caff" opacity=".2"/><path d="m46 125 132-55 100 35-133 58Z" fill="#d8ebff" opacity=".5"/><path d="m255 45 47-18 56 23-48 18Z" fill="#dceeff"/><path d="m255 45 55 23v50l-55-22Z" fill="#c5dfff" opacity=".7"/><path d="m310 68 48-18v51l-48 17Z" fill="#b4d8ff" opacity=".4"/></svg>
  </div>
</template>
