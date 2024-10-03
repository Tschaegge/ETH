package ch.ethz.rse.integration.tests;

import ch.ethz.rse.Store;

// expected results:
// NON_NEGATIVE UNSAFE
// FITS_IN_TROLLEY UNSAFE
// FITS_IN_RESERVE UNSAFE

public class Basic_Loop_Test {

  public static void m1() {
    Store s = new Store(2, 4);
    
    for (int i = -2; i < 10; i++) {
      s.get_delivery(i);
    }
  }
}