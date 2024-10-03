package ch.ethz.rse.integration.tests;

import ch.ethz.rse.Store;

// expected results:
// NON_NEGATIVE SAFE
// FITS_IN_TROLLEY SAFE
// FITS_IN_RESERVE SAFE

public class NonNegative_Test_IfT {

  public static void m1() {
    Store s = new Store(2, 4);
    int x = 13;
    if(4*4<x){
        s.get_delivery(-1);
    }else{
        s.get_delivery(1);
    } 
  }
}