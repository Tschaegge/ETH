package ch.ethz.rse.integration.tests;

import ch.ethz.rse.Store;

// expected results:
// NON_NEGATIVE UNSAFE
// FITS_IN_TROLLEY UNSAFE
// FITS_IN_RESERVE UNSAFE

public class Test_Parameter {

  public static void m1(int j) {
    Store s = new Store(2, 4);

    s.get_delivery(j);
    
  }
}
