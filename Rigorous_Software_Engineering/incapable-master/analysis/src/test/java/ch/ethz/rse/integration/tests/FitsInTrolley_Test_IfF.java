package ch.ethz.rse.integration.tests;

import ch.ethz.rse.Store;

// expected results:
// NON_NEGATIVE SAFE
// FITS_IN_TROLLEY UNSAFE
// FITS_IN_RESERVE SAFE

public class FitsInTrolley_Test_IfF {

  public static void m1() {
    Store s = new Store(2, 4);
    int x = 2;
    if(x!=0){
        s.get_delivery(3);
    }else{
        s.get_delivery(2);
    }
  }
}
