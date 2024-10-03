package ch.ethz.rse.integration.tests;

import ch.ethz.rse.Store;

// expected results:
// NON_NEGATIVE SAFE
// FITS_IN_TROLLEY SAFE
// FITS_IN_RESERVE UNSAFE

public class FitsInReserve_Test_If {

  public static void m1() {
    Store s = new Store(10, 10);
    boolean b = true;
    if (!b) {
        s.get_delivery(5);
    }else{
        s.get_delivery(9);
    }

    if (b) {
        s.get_delivery(2);
    } else {
        s.get_delivery(0);
    }
    
    s.get_delivery(1);
  }
}

