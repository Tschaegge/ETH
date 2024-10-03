
package ch.ethz.rse.integration.tests;

import ch.ethz.rse.Store;

// expected results:
// NON_NEGATIVE SAFE
// FITS_IN_TROLLEY SAFE
// FITS_IN_RESERVE SAFE

public class Insane_NEST {
  public static void m1(){
    Store s = new Store(1, 10);
    for (int i = 0; i < 2; i++) {
      for (int j = 0; j < 2; j++) {
        s.get_delivery(i * j);
      }
    }
 }
}

