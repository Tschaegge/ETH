package ch.ethz.rse.integration.tests;

import ch.ethz.rse.Store;

// expected results:
// NON_NEGATIVE SAFE
// FITS_IN_TROLLEY SAFE
// FITS_IN_RESERVE SAFE

public class Basic_IF_Test_2 {

  public void m1() {
    Store s = new Store(2, 4);
    int a = 1;
    int b = 2;
    if(((a * 2) - 1) >= (b * 1 - a)){
      s.get_delivery(1);
    }
      s.get_delivery(1);

      if(((a * 2) + 1) <= (b * 2 - a)){
        s.get_delivery(1);
      }
    
    Store s2 = new Store(4, 4);
    s2.get_delivery(4);
  }
}