import React from "react";
import { Composition } from "remotion";
import { StoryRunner, StoryRunnerProps } from "../engine/loader/StoryRunner";
import { BridgeShort } from "./videos/bridge/Bridge";
import { BridgeShort as TheGlitchThatSpawnedAnEntireVirtualEcosystem } from "./videos/the_glitch_that_spawned_an_entire_virtual_ecosystem/Bridge";
import { BridgeShort as TheGlitchThatAccidentallyInventedOpenWorldGaming } from "./videos/the_glitch_that_accidentally_invented_open_world_gaming/Bridge";
import { BridgeShort as TheGlitchThatSpawnedABillionDollarEmpire } from "./videos/the_glitch_that_spawned_a_billion_dollar_empire/Bridge";

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="StoryComposition"
        component={StoryRunner as unknown as React.FC<Record<string, unknown>>}
        durationInFrames={300}
        fps={30}
        width={1080}
        height={1920}
        defaultProps={{
          storyId: "default",
          title: "Generated Story",
          shots: [],
        } satisfies StoryRunnerProps}
      />
      <Composition
        id="BridgeShort"
        component={BridgeShort}
        durationInFrames={2010}
        fps={30}
        width={1080}
        height={1920}
      />
      <Composition
        id="the-glitch-that-spawned-a-billion-dollar-empire"
        component={TheGlitchThatSpawnedABillionDollarEmpire}
        durationInFrames={2010}
        fps={30}
        width={1080}
        height={1920}
      />
      <Composition
        id="the-glitch-that-accidentally-invented-open-world-gaming"
        component={TheGlitchThatAccidentallyInventedOpenWorldGaming}
        durationInFrames={2010}
        fps={30}
        width={1080}
        height={1920}
      />
      <Composition
        id="the-glitch-that-spawned-an-entire-virtual-ecosystem"
        component={TheGlitchThatSpawnedAnEntireVirtualEcosystem}
        durationInFrames={2010}
        fps={30}
        width={1080}
        height={1920}
      />
    </>
  );
};
