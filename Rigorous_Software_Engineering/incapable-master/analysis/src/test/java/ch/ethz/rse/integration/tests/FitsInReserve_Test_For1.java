package ch.ethz.rse.integration.tests;

import ch.ethz.rse.Store;

// expected results:
// NON_NEGATIVE SAFE
// FITS_IN_TROLLEY SAFE
// FITS_IN_RESERVE UNSAFE

public class FitsInReserve_Test_For1 {

  public static void m1() {
    Store s = new Store(2, 5);

    for (int index = 0; index < 3; index++) {
        s.get_delivery(2);
    }

  }
}

