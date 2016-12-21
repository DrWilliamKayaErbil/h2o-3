package ai.h2o.cascade.stdlib.frame;

import ai.h2o.cascade.core.CFrame;
import ai.h2o.cascade.stdlib.StdlibFunction;

/**
 * Number of rows in a frame.
 */
public class FnNrows extends StdlibFunction {

  public long apply(CFrame frame) {
    return frame.nRows();
  }

}
