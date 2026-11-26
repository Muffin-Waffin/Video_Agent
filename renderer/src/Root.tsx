import React from "react";
import { Composition } from "remotion";
import { StoryRunner, StoryRunnerProps } from "../engine/loader/StoryRunner";
import { BridgeShort } from "./videos/bridge/Bridge";

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
    </>
  );
};
